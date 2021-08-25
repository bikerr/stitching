import cv2
import numpy as np


def thresh2(img):
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    not_gray = cv2.bitwise_not(gray)
    h, w = gray.shape
    a = [0 for z in range(0, h)]
    for j in range(0, h):
        # if np.var(not_gray[j]) < 5:
        #     a[j] = 0
        #     continue
        # else:
            for i in range(0, w):
                a[j] += not_gray[j, i]

    a = np.array(a)
    cv2.normalize(a, a, 0, w, cv2.NORM_MINMAX)
    thresh = np.ones((h, np.max(a)))*255

    for j in range(0, h):
        for i in range(0, a[j]):
            thresh[j, i] = 0
    image = np.ones((h, w * 2))
    image[0:h, 0:w] = gray
    image[0:h, w:2*w] = thresh
    return a, image


# 水平方向投影匹配拼接
def stitch(img1, img2):
    if img1 is None or img2 is None:
        raise FileNotFoundError

    if img1.shape != img2.shape:
        raise ValueError

    th1, image1 = thresh2(img1)
    th2, image2 = thresh2(img2)

    h, w, c = img2.shape

    image1AndImage2 = np.ones((h, image1.shape[1] + image2.shape[1]))
    image1AndImage2[0:h, 0:image1.shape[1]] = image1
    image1AndImage2[0:h, image1.shape[1]:image1.shape[1] + image2.shape[1]] = image2

    window = h // 20

    top = window
    bottom = window

    dst = np.ones(((h - window) // 10 + 1, (h - window) // 10 + 1)) * 255

    for i in range(h - window - 1 - bottom, top, -10):
        for j in range(top, h - window - 1 - bottom, 10):
            dst[i // 10, j // 10] = np.max(np.abs(th1[i: i + window] - th2[j: j + window]))

    dstMin, dstMax, dstMinLoc, _ = cv2.minMaxLoc(dst)

    featureMin = 1000
    image1Height = 0
    image2Height = 0
    for i in range(0, 9):
        for j in range(0, 9):
            feature1 = th1[dstMinLoc[1] * 10 + i:dstMinLoc[1] * 10 + i + window]
            feature2 = th2[dstMinLoc[0] * 10 + j:dstMinLoc[0] * 10 + j + window]
            if np.max(np.abs(feature1 - feature2)) < featureMin:
                featureMin = np.max(np.abs(feature1 - feature2))
                image1Height = dstMinLoc[1] * 10 + i
                image2Height = dstMinLoc[0] * 10 + j

    print("best match ", dstMin, dstMinLoc, "window:", window, image1Height, image2Height, bottom, top)

    print("mean",
          np.mean(th1[image1Height:image1Height + window] - th2[image2Height:image2Height + window]),
          np.var(th1[image1Height:image1Height + window] - th2[image2Height:image2Height + window]),
          )

    if np.var(th1[image1Height:image1Height + window] - th2[image2Height:image2Height + window]) > 100:
        return 0, image1Height / h, image2Height / h
    return 1, image1Height/h, image2Height/h


# 去重模板匹配法
def stitch2(img1, img2, ratio):
    if img1 is None or img2 is None:
        raise FileNotFoundError
    if img1.shape != img2.shape:
        raise ValueError

    # 考虑到旁边滑动条影响 左右个去处20像素进行匹配
    img1 = img1[0:img1.shape[0], 20:img1.shape[1] - 20, 0:img1.shape[2]]
    img2 = img2[0:img2.shape[0], 20:img2.shape[1] - 20, 0:img2.shape[2]]

    if img1.shape[2] == 3:
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    else:
        gray1 = img1
        gray2 = img2

    h, w = gray1.shape

    thresh1 = cv2.adaptiveThreshold(gray1, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    thresh2 = cv2.adaptiveThreshold(gray2, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)

    height = h
    sub = thresh1 - thresh2
    sub = cv2.medianBlur(sub, 3)
    sub = sub // 255
    thresh = w // 10
    # 考虑到部分机型底部刘海问题 或者有滑动条等问题 去除掉底部3%的位置开始匹配
    min_height = h*0.97
    for i in range(h - 1, 0, -1):
        if np.sum(sub[i]) > thresh and height < min_height:
            print(np.sum(sub[i]))
            break
        height = height - 1
    block = sub.shape[0] // ratio

    templ = gray1[height - block:height, ]
    res = cv2.matchTemplate(gray2, templ, cv2.TM_SQDIFF_NORMED)
    mn_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    print("thresh, shape ,height, block", thresh, sub.shape, height, block)
    print("mn_val, max_val, min_loc, max_loc", mn_val, max_val, min_loc, max_loc)

    # 考虑到JPG 可能存在成像压缩，至少需要95的相似度才认为匹配成功
    if mn_val < 0.05:
        return 1, (height - block) / h, min_loc[1] / h
    else:
        return 0, 1, 0


def draw(img1, img2):
    h, w, c = img2.shape

    result, bottom, top = stitch2(img1, img2, 15)

    bottom = int(bottom * h)
    top = int(top * h)

    roi1 = img1[0:bottom, ]
    roi2 = img2[top:h, ]

    image = np.ones((roi1.shape[0] + roi2.shape[0], w, 3))
    image[0:roi1.shape[0], 0:w, 0:3] = roi1
    image[roi1.shape[0]:roi1.shape[0] + roi2.shape[0], 0:w, 0:3] = roi2
    return image


if __name__ == "__main__":
    img1 = cv2.imread("./imgs/1.jpg")
    img2 = cv2.imread("./imgs/2.jpg")
    dst = draw(img1, img2)
    cv2.imwrite("result/1.jpg", dst)

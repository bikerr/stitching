# stitching
picsew 滚动截屏 图片拼接 长图拼接 智能拼图 stitch opencv python 拼长图  拼截屏 拼聊天记录

### 效果
- eg

![image1](./imgs/1.jpg)![image2](./imgs/2.jpg)

- 效果

![result](./result/1.jpg)

## 实现方案
### 方案一
- stitch1 水平方向投影匹配拼接

### 方案二
- stitch2 去重模板匹配法 测试效果比方案一好

### TODO:
- 计算效率问题 可以进行缩放图片进行拼接 效率可能会高
- 准确度问题 目前方案二去重图片重复的底部进行拼接 存在某些场景无法缝合问题
- 拼接边缘融合 边缘融合效果可以达到更好的拼接效果
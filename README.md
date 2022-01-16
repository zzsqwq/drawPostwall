# drawPostwall

A script to draw a simple picture for [Postwall-MiniApp](https://github.com/zzsqwq/Postwall-MiniApp)

## Usage
运行 `python3 main.py --test` 使用本地目录下的 `test_data.json` 生成测试图

运行 `python3 main.py` 使用 `Flask` 运行服务器接口
```shell
> python main.py --help
usage: main.py [-h] [--test]

optional arguments:
-h, --help  show this help message and exit
--test      if test or not
```

## Example
![](example.png)

## Future

+ [ ] 生成图片大小/比例可配置
+ [ ] 二维码可配置
+ [ ] 颜色可配置
+ [ ] test 可指定测试数据
+ [ ] test 指定是否生成图片

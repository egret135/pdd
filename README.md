# 拼多多
拼多多日结算单采集

```shell script
# ~ python pdd.py -h
                                                                      
usage: pdd.py [-h] -m MONTH -u USERNAME -p PASSWORD [-b BINARY_LOCATION] [-d] [-c CALLBACK_URL]

optional arguments:
  -h, --help            show this help message and exit
  -m MONTH, --month MONTH
                        抓取时间，格式为：Y-m
  -u USERNAME, --username USERNAME
                        拼多多商家账号
  -p PASSWORD, --password PASSWORD
                        拼多多商家密码
  -b BINARY_LOCATION, --binary-location BINARY_LOCATION
                        浏览器可执行文件路径
  -d, --headless        不开启浏览器执行程序
  -c CALLBACK_URL, --callback-url CALLBACK_URL
                        结果数据回调链接
```

```shell script
python pdd.py -m 2021-03 -u 'username' -p 'password' -d -c 'https://www.baidu.com'
```
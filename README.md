# hpoc
简易批量漏洞测试

```
hpoc.py -h
```
![image](https://github.com/hhxdi/hpoc/assets/72481638/7aa369ad-2ce1-4532-8dc3-6cad91177aac)

直接运行hpoc 默认使用当前目录的1.txt和url.txt

1.txt内容是简单的请求包，不需要修改什么
![image](https://github.com/hhxdi/hpoc/assets/72481638/6d6ede99-7dca-4510-9471-e711fac2925e)

url.txt 每行一个url 
![image](https://github.com/hhxdi/hpoc/assets/72481638/6019bc89-08bb-479c-a540-7a91b8d89838)

运行结果：
![image](https://github.com/hhxdi/hpoc/assets/72481638/ae5bcbcd-7990-427d-87ee-d5faeeda7f03)

其他命令：hpoc.py -u xx.csv  xx.csv 支持fofa和hunter的导出结果 其他csv在url的那栏改成link也可以
需要的库在requirement.txt

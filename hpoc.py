# coding:utf-8
import string
import ipaddress
import random
import re
import threading
from urllib.parse import urlparse
import pandas as pd
import yaml
import requests
import time
import os
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore")

class MyThread(threading.Thread):
    def __init__(self, func, args):
        threading.Thread.__init__(self)  # 调用父类的构造函数
        self.args = args
        self.func = func
    def run(self):  # 线程活动方法
        self.result = self.func(*self.args)  # 启动这个函数args是元组，取出url
    def get_result(self):
        threading.Thread.join(self)
        try:
            return self.result
        except Exception:
            return None
class tools():
    # 去除换行
    def __init__(self):
        pass

    def remove_indentation(self, text):
        lines = text.split('\n')
        cleaned_lines = [line.lstrip() for line in lines]
        if lines[len(lines) - 1].strip():
            pass
        result = '\n'.join(cleaned_lines[1:])
        return result

    # POC文本处理
    def Poctext_deal(self, text, host=False):
        temp = [i for i in text.split("\n") if i != ""]
        data = None
        if "\n\n" in text:
            headers, data = text.split('\n\n', 1)
            header_lines = headers.split('\n')
        else:
            header_lines = temp
        # 解析请求头
        count = 0
        if len(header_lines[0]) == 0:
            first_line = header_lines[1]
            count += 1
        else:
            first_line = header_lines[0]
        method, path, protocol = first_line.split()

        header_dict = {}
        for line in header_lines[count + 1:]:
            if len(line.split(': ', 1)) == 1:
                key, value = line.split(':', 1)
            else:
                key, value = line.split(': ', 1)
            header_dict[key] = value
        try:
            if not host:
                header_dict["Host"] = ""
                header_dict.pop("Host")
        except Exception as e:
            print(e)
        return path, method, header_dict, data, protocol

    def pot_to_poc(self, path, method, header_dict, data, protocol, host):
        if type(path) == type(""):
            txt = ""
            txt += " ".join([method, path, protocol]) + "\n"
            header_dict["Host"] = host
            txt += "\n".join(["{}: {}".format(key, value) for key, value in header_dict.items()]) + "\n"
            txt += "\n" + data
            return txt
        if type(path) == type([]):
            txts = []
            for i in range(len(path)):
                txt = ""
                txt += " ".join([method[i], path[i], protocol[i]]) + "\n"
                # header_dict[i]["Host"] = ""
                txt += "\n".join(["{}: {}".format(key, value) for key, value in header_dict[i].items()]) + "\n"
                txt += "\n" + data[i]
                txts.append(txt)
            return txts

    # 代替随机字符   匹配 {{xxx}} 格式的内容
    def replace_variables_with_random(self, text):
        variable_dict = {}  # 用于跟踪变量和生成的随机字符串的映射

        def replace(match):
            # 获取 {{xxx}} 中的内容
            variable_content = match.group(1)
            # 如果变量已经有对应的随机字符串，则直接使用
            if variable_content in variable_dict:
                return variable_dict[variable_content]

            # 生成随机字符串
            random_str = generate_random_string(len(variable_content))

            # 将变量和对应的随机字符串加入字典
            variable_dict[variable_content] = random_str

            return random_str

        def generate_random_string(length):
            characters = string.ascii_letters + string.digits
            return ''.join(random.choice(characters) for _ in range(length))

        # 匹配 {{xxx}} 格式的内容
        pattern = r'\{\{(.+?)\}\}'
        # 使用 replace 函数替换匹配到的内容
        result = []
        for t in text:
            result.append(re.sub(pattern, replace, t))
        return result

    # 读取yaml 种的 raw
    def find_key_recursive(self, data, target_key, ):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == target_key:
                    return value
                elif isinstance(value, (dict, list)):
                    result = self.find_key_recursive(value, target_key)
                    if result is not None:
                        return result
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    result = self.find_key_recursive(item, target_key)
                    if result is not None:
                        return result

    def text_frompoctext(self, poctext):
        paths, methods, datas, headers = [[] for i in range(4)]
        Ts, spendtimes, statuscodes, timeouts = [[] for i in range(4)]
        protocols = []
        raws = None
        try:
            yamldata = yaml.safe_load(poctext)
            raws = self.find_key_recursive(yamldata, 'raw')
        except:
            pass
        parsed_url = urlparse(poctext)
        path = parsed_url.path + "?" + parsed_url.query
        if raws != None and len(raws) > 0:
            raws = self.replace_variables_with_random(raws)
            for raw in raws:
                # return path, method, header_dict, data, protocol
                path, method, header, data, protocol = self.Poctext_deal(raw)
                paths.append(path), methods.append(method)
                headers.append(header), datas.append(data)
                protocols.append(protocol)
        elif parsed_url.hostname != None and poctext != "\n":
            paths.append(path), methods.append("GET")
            headers.append({}), datas.append(None)
            protocols.append("HTTP/1.1")
        else:
            poctext = self.replace_variables_with_random([poctext])[0]
            path, method, header, data, protocol = self.Poctext_deal(poctext, host=True)
            paths.append(path), methods.append(method)
            headers.append(header), datas.append(data)
            protocols.append(protocol)
        for i in range(len(paths)):
            Ts.append(""), spendtimes.append(100)
            statuscodes.append(None), timeouts.append(10)
        result = [paths, methods, datas, headers, Ts, spendtimes, statuscodes, timeouts, protocols]
        return result

    def rand_agent(self):
        from fake_useragent import UserAgent
        ua = UserAgent()
        header = {"User-Agent": ua.random}
        return header

    def is_domain(self, url):

        parsed_url = urlparse(url)
        try:
            # Attempt to create an IPv4 or IPv6 address object
            ipaddress.ip_address(parsed_url.hostname)
            return False  # If successful, it's an IP address
        except ValueError:
            return bool(parsed_url.hostname)

    def get_url_icp(self, url):
        try:
            headers = self.rand_agent()
            parsed_url = urlparse(url)
            if not self.is_domain(url):
                return None, None
            url = "https://icp.chinaz.com/" + parsed_url.netloc
            # 发送HTTP请求获取网页内容
            # print(url)
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 检查是否请求成功
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            # 提取标题
            try:
                company_name = soup.find('a', id='companyName').text
                fwone = soup.select_one('li.clearfix p strong.fl.fwnone').text

            except:
                company_name = ""
                fwone = ""
            return company_name, fwone

        except requests.exceptions.RequestException as e:
            # print("Error fetching page:",e)
            return None

    def get_page_title(self, url):
        try:
            # 发送HTTP请求获取网页内容
            response = requests.get(url, verify=False)
            response.raise_for_status()  # 检查是否请求成功

            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题
            title = soup.title.string.strip() if soup.title else "No title found"

            return title

        except requests.exceptions.RequestException as e:
            print("Error fetching page: ",e)
            return None

    def get_url_information(self, url):
        company_name, fwone, title = None, None, None
        try:
            company_name, fwone = self.get_url_icp(url)
            title = self.get_page_title(url)
        except Exception as e:
            print(e)
        return company_name, fwone, title

    def is_valid_regex(self, input_string):
        pattern = r'\{\{(.+?)\}\}'  # 匹配形如{{xxx}}的模式，并捕获其中的xxx部分
        match = re.search(pattern, input_string)
        if match:
            return match.group(1)  # 返回捕获的内容
        else:
            return False

    def find_matches(self, regex_pattern, text):
        matches = re.findall(regex_pattern, text)
        if len(matches) > 1:
            return matches[0]
        else:
            return None

    def Get_urls(self,path):
        if path.endswith('.txt'):
            with open(path, "r", encoding="utf-8", errors="gbk") as f:
                lines = f.readlines()
            lines = [line.strip() for line in lines]
            return lines
        else:
            data = pd.read_csv(path)
            if "link" in data.columns.values:
                return data["link"].values
            elif "url" in data.columns.values:
                return data['url'].values
class http(tools):
    def __init__(self,queue=None):
        super().__init__()
        self.count = 0
    def save_to_csv(self, over,filename,filepath):
        df = pd.DataFrame(over)
        current_time_struct = time.localtime()
        folder_path = "result/"
        os.makedirs(folder_path, exist_ok=True)
        ymd = folder_path + time.strftime("%Y-%m-%d", current_time_struct) + "/"
        os.makedirs(ymd, exist_ok=True)
        file = ymd + "/" + filename
        # 根据时间创建新及临时文件
        if filepath != None:
            if len(filepath) > 1:
                os.makedirs(filepath,exist_ok=True)
                file = filepath + "/" + filename + "-" + time.strftime("%H-%M-%S", current_time_struct) + ".csv"
        if len(over) == 0:
            print("所有网址已测试，没有发现存在问题网址。请求包或者资产可能出现问题")
        else:
            print(file)
            df.to_csv(file, index=False)
        print("Over！")

    def find_matches(self,regex_pattern, text):
        matches = re.findall(regex_pattern, text)
        if len(matches) > 1:
            return matches[0]
        else:
            return None
    # 去除
    def Remove_None(self, ls):
        ls = [i for i in ls if i != None]
        return ls

    def Remove_page(self, page, temp=None):
        http_status_codes = ["访问禁止", "禁止", "<title>404</title>", "location.href", "Burp", "会话登录过期"]
        if temp != None:
            for i in temp:
                http_status_codes.append(i)
        for code in http_status_codes:
            if code in page:
                return False
        return True

    def formdatacl(self,data):
        temp = "\r\n".join(data.split("\n"))
        return temp

    # 修改 ---> n 个 test 传入的参数都应该是列表 除了proxies 其他的都是列表 然后直接循环判断
    def request_T(self,url, method, data, headers, T="", spendtime=100, statuscode="", timeout=10,ze=None, proxies=None):
        start_time = time.time()
        if data != None and data != "":
            data = self.formdatacl(data)
        try:
            if method == "GET":
                resp = requests.get(url, data=data, headers=headers, proxies=proxies, verify=False, allow_redirects=False,
                                    timeout=timeout)
            else:
                resp = requests.post(url, data=data, headers=headers, proxies=proxies, verify=False, allow_redirects=False,
                                     timeout=timeout)
        except TimeoutError:
            return [None,None,None,None,None]

        if statuscode == "" or statuscode == None:
            statuscode = [200, 500]
            if resp.status_code in statuscode:
                '''company, fwon = self.get_url_icp(url)
                if self.Remove_page(resp.text):
                     return None'''

                ysurl = re.match(r"(?P<scheme>https?://)?(?P<netloc>[\w\.-]+)", url)[0]
                print(ysurl + " maybe has the problem")
                if T != "":
                    if T in resp.text:
                        return [ysurl,url, resp.text[:5000]]#,company,fwon,T]
                    if ze != None or len(ze) != 0:
                        match = self.find_matches(ze,resp.text)
                        return [ysurl,url, resp.text[:5000]]
                else:
                    return [ysurl,url, resp.text[:5000]]
        end_time = time.time()
        spend = end_time - start_time
        if spend > spendtime:
            company, fwon = self.get_url_icp(url)
            return [url, resp.text[:5000], company, fwon,spend]

        return [None,None,None,None,None]

    def pocs(self,urls, paths, methods, datas, headers,
             Ts, spendtimes, statuscodes, timeouts,zes=None, proxies=None):

        results = []
        if zes == None:
            zes = [""]
        for url in urls:
            for i in range(len(paths)):
                up = url + paths[i]
                try:
                    # 进度条
                    self.count += 1
                    time.sleep(0.01)
                    # 参数 方法，数据，请求头，特征，花费事件，状态，最长响应事件，代理
                    method, data, header = methods[i], datas[i], headers[i]
                    T, spendtime, statuscode, timeout = Ts[i], spendtimes[i], statuscodes[i], timeouts[i]
                    ze = zes[i]
                    temp = self.request_T(up,method, data, header, T, spendtime, statuscode, timeout,ze, proxies)
                    results.append(temp)
                except Exception as e:
                    pass

        result = self.Remove_None(results)
        return result

    def MutilThread(self, urls, paths, methods, datas, headers,Ts,spendtimes,statuscodes,
                    timeouts, proxy=None, n=3,filename=None,filepath=None, file=True):
        # 多线程
        start_time = time.time()
        threadList = []
        step = len(urls) // n
        # 数据分段 添加进程池

        us = [urls[i:i + step] for i in range(0, len(urls), step)]
        threadList = [MyThread(self.pocs, (urls, paths, methods, datas, headers,
                                           Ts,spendtimes,statuscodes,timeouts, proxy,)) for urls in us]

        print(len(threadList))
        for t in threadList:
            t.setDaemon(True)  # 设置守护线程，父线程会等待子线程执行完后再退出
            t.start()  # 线程开启
        for i in threadList:
            i.join()  # 等待线程终止，等子线程执行完后再执行父线程

        # 结果处理
        results = []
        for temp in threadList:
            results.append(temp.get_result())
        over = []
        for temp1 in results:
            try:
                for temp2 in temp1:
                    if temp2.count(None) == len(temp2):
                        continue
                    over.append(temp2)
            except:
                pass
        # 输出后保存
        end_time = time.time()
        sp = end_time-start_time
        print(str(len(over)) + " 个网址可能存在问题." + "\n费时:"+ str(sp) + "s")
        # 保存
        if file:
            self.save_to_csv(over,filename,filepath)

    def run(self,Text_poc,urls,n,filename=None,special=None,proxies=""):


        result = self.text_frompoctext(Text_poc)
        paths, methods, datas, headers, Ts, spendtimes, statuscodes, timeouts, _ = [i for i in result]
        if 0 < len(urls) < n:
            n = len(urls)
        if n == 1:
            print("单线程")
            if len(proxies) == 0:
                self.pocs(urls, paths, methods, datas, headers,
                             Ts, spendtimes, statuscodes, timeouts, proxies=None)
            else:
                self.pocs(urls, paths, methods, datas, headers,
                             Ts, spendtimes, statuscodes, timeouts, proxies=proxies)
        else:
            print(str(n)+"线程")
            for i in range(len(headers)):
                try:
                    if "Host" in headers[i]:
                        headers[i].pop("Host")
                except Exception as e:
                    pass
                    # print(e)
            if len(proxies) == 0:
                self.MutilThread(urls, paths, methods, datas, headers, Ts, spendtimes, statuscodes,
                                    timeouts, proxy=None, n=n, filename=filename, filepath=None, file=True)
            else:
                self.MutilThread(urls, paths, methods, datas, headers, Ts, spendtimes, statuscodes,
                                    timeouts, proxy=proxies, n=n, filename=filename, filepath=None, file=True)
class run(tools):
    def __init__(self, pocpath, urlpath, n):
        super().__init__()
        self.pocpath = pocpath
        self.urlpath = urlpath
        self.n = n

    def run(self):
        filename = str(int(time.time())) + ".csv"
        special = None
        urls = self.Get_urls(self.urlpath)
        poctext = "\n".join(self.Get_urls(self.pocpath))
        n = self.n
        proxies = ''
        self.request_poc([poctext,urls,n,filename,special,proxies])
    def request_poc(self, *args):
        session = http()
        _ = args[0]
        Poctext, urls, n, filename, special, proxies = _
        try:
            session.run(Poctext, urls, n, filename, special, proxies)
        except Exception as e:
            pass
            # e = str(e)
            # print(e)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='案例/ps：./hpoc.py -p 1.txt -u urls.txt')
    parser.add_argument('-p', '--poc', default='./1.txt')
    parser.add_argument('-u', '--url', default='./urls.txt')
    parser.add_argument('-n', '--num', default=76, type=int)

    args = parser.parse_args()
    pocpath = args.poc
    urlpath = args.url
    n = args.num
    print(pocpath,urlpath)
    RUN = run(pocpath, urlpath, n)
    RUN.run()
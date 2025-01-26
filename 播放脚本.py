import os
import time

import pyperclip
from pynput import mouse
from threading import Thread
import pyautogui
import keyboard
import sys

num = 1
mouse_xy_dict = {}
times = [time.time()]
EXIT = False


def read_config(file_name):
    global num
    if_=None
    with open(file_name, 'r', encoding='utf-8') as file:
        begin = False
        for line in file:
            if "begin" in line and not begin:
                begin = True
                if num == 1:
                    print("脚本开始第{0}次执行".format(num))
                else:
                    print("再来一次！ 开始执行第{0}次".format(num))
                continue

            if begin:
                if "again" in line:
                    file.close()
                    num += 1
                    return "again"  # 表示重新开始读取配置文件
                if "if" in line:
                    print("判断为",end=' ')
                    var = line_to_var(line)
                    if var[1]=="clipboard":
                        if judge_clipboard(var[2:]):
                            print("True")
                            if_ = True # 判断是否执行脚本里面的if
                        else:
                            print("False")
                            if_ = False
                if if_ is not None:
                    if not if_:
                        if "end" in line:
                            if_ = True
                        continue

                if "//" in line:  # 代表该行为注释，跳过
                    continue

                if "wait_key" in line:
                    s = line_to_var(line)
                    print("等待按下", str(s[1]))
                    wait_for(s[1])
                    continue
                if "wait_mouse" in line:
                    s = line_to_var(line)
                    wait_for_mouse(float(s[1]))
                    continue
                if "get_xy" in line:
                    var = line_to_var(line)
                    get_xy(var[1])
                    continue
                if "set_xy" in line:
                    var = line_to_var(line)
                    set_xy(var[1])
                    continue
                if "mouse_down" in line:
                    var = line_to_var(line)
                    mouse_down(var[1])
                    continue
                if "mouse_up" in line:
                    var = line_to_var(line)
                    mouse_up(var[1])
                    continue
                if "scroll" in line:
                    var = line_to_var(line)
                    mouse_scroll(var[1])
                    continue
                if 'paste' in line:
                    var=line_to_var(line)
                    time.sleep(0.1)
                    text = pyperclip.paste()
                    print("剪切板内容：\n",text)
                    if len(var)==0:
                        keyboard.send('ctrl+v')
                        continue
                    text=text.split('\n')
                    if var[1]>len(text):
                        print("您要求粘贴剪切板的第{0}行，但剪切板只有{1}行".format(var[1],len(text)))
                        continue
                    pyautogui.write(text[var[1]-1])
                    continue

                try:
                    # 将配置字符串转换为元组，并添加到配置列表中
                    config_tuple = line_to_var(line)
                    if config_tuple[0] == 0:
                        execute_click(config_tuple)
                    if config_tuple[0] == 1:
                        execute_key(config_tuple)
                except SyntaxError:
                    print(f"配置文件中存在语法错误: {line}")

    return 'end'


def judge_clipboard(arg):
    time.sleep(0.1)
    text = pyperclip.paste()

    if arg[0] == "has":

        if arg[1] in text:
            return True
        else:
            return False



def line_to_var(s):
    s = s.strip()[1:-1]
    items = s.split(',')
    result = []
    for item in items:
        # 去除项的前后空格和引号
        item = item.strip().strip('"')
        # 判断是否是浮点数
        if '.' in item:
            try:
                result.append(float(item))
            except ValueError:
                result.append(item)
        else:
            try:
                result.append(int(item))
            except ValueError:
                result.append(item)
    return result


def mouse_down(button):
    if "l" in button:
        pyautogui.mouseDown(button="left")
    if "r" in button:
        pyautogui.mouseDown(button="right")


def mouse_up(button):
    if "l" in button:
        pyautogui.mouseUp(button="left")
    if "r" in button:
        pyautogui.mouseUp(button="right")


def mouse_scroll(step):
    pyautogui.scroll(step)


def get_xy(var_name):

    mouse_x, mouse_y = pyautogui.position()
    mouse_xy_dict[var_name] = [mouse_x, mouse_y]
    print("成功保存当前鼠标位置为“{0}”  {1}".format(var_name, mouse_xy_dict[var_name]))


def set_xy(var_name):
    try:
        pyautogui.moveTo(x=mouse_xy_dict[var_name][0], y=mouse_xy_dict[var_name][1])
        print("设置鼠标位置为“{0}”  {1}".format(var_name, mouse_xy_dict[var_name]))
    except KeyError:
        print("位置“{0}”不存在，请检查是否保存该位置".format(var_name))


def wait_for(key):
    keyboard.wait(key)


def on_click_factory(delay_time):  # 监听鼠标库不支持传额外参数，使用工厂函数解决
    def on_click(x, y, button, pressed):
        times.append(time.time())
        timestamp = times[-1] - times[-2]
        if len(times) > 3:
            times.pop(0)
        if timestamp >= delay_time:  # 如果间隔超过0.5，认为用户复制了文子
            if not pressed:  # 检查鼠标按钮是否释放
                return False  # 返回 False 停止监听

    return on_click


def wait_for_mouse(delay_time):
    print(f"等待鼠标按下超过{delay_time}秒继续执行")
    custom_on_click = on_click_factory(delay_time=delay_time)
    # 创建监听鼠标事件的对象
    listener = mouse.Listener(on_click=custom_on_click)
    listener.start()  # 启动监听器
    listener.join()  # 等待监听器线程终止


def execute_click(config):
    """根据配置执行操作"""
    start_time = time.time()
    (type, timestamp, x, y, duration, *values) = config
    while time.time() - start_time < timestamp:
        time.sleep(0.01)  # 每次检查间隔0.1秒
    print(f"Step({x},{y}) {', '.join(map(str, values))}")
    pyautogui.click(x=x, y=y, duration=duration)


def execute_key(config):
    """根据配置执行操作"""
    start_time = time.time()
    (event_type, timestamp, key, duration, *values) = config
    while time.time() - start_time < timestamp:
        time.sleep(0.01)  # 每次检查间隔0.1秒
    print(f"Step({key}) {', '.join(map(str, values))}")
    keyboard.send(key)


def exit_program():
    global EXIT
    keyboard.wait("ctrl+q")
    EXIT = True
    sys.exit()


if __name__ == "__main__":
    Quit = Thread(target=exit_program)
    Quit.start()
    config_file = ''
    # 获取当前目录下所有 .sk 文件
    sk_files = [f for f in os.listdir('.') if f.endswith('.sk')]

    if not sk_files:
        input("没有找到 .sk 配置文件 \n请根据使用手册编写配置文件或使用录制脚本录制后重新打开本软件")
        EXIT = True
    else:
        # 显示文件列表供用户选择
        print("请选择一个 .sk 文件:")
        for idx, filename in enumerate(sk_files):
            print(f"{idx + 1}: {filename}")

        # 用户选择文件
        choice = int(input("请输入执行文件编号: ")) - 1

        if 0 <= choice < len(sk_files):
            config_file = sk_files[choice]
            print(f"读取配置文件: {config_file}")
        else:
            print("无效的选择，程序退出。")
            EXIT = True

    while not EXIT:
        configs = read_config(config_file)
        if configs == "again":
            continue  # 如果配置文件中有 (again)，重新开始读取配置文件
        if configs == "end":
            print("脚本结束")
        break
    sys.exit()
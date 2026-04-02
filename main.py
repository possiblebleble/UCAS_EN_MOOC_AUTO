'''
PLEASE READ ME 请阅读以下内容：
    1.本代码是基于前人成果的修改调整，"https://github.com/HangboZhu/ucas-mooc-automate"，在此感谢 Hangbo Zhu 同志；
    2.在运行前人代码时发现了一些问题，包括 无法倍速、重复播放等，可能并非代码所致，为学习通网页相关；

    3.本代码作出一些调整、修改：
    A 将URL(课程链接)的填写放到了代码中；
    B 取消了对文档的操作，请用户去移动平台自行完成文档任务点【网页端疑似无法实现】【点一下就行很快的】；
    C 保障视频二倍速的稳定；
    D 用户自由选择从哪一章节开始，随后按顺序进行，无视文档和 QUIZ；
    E 允许使用 P 键暂停，后可重新指定从哪一章节继续；

    4.如何使用：
    step 1 ：明确 python 3.7+ 、相关库 、 Chrome 浏览器 已到位；
    step 2 ：登陆 国科大在线/学习通 ，去英语mooc的刷课页面 复制链接 到代码 'DEFAULT_URL'中；
    step 3 ：运行代码 (建议不要在VPN环境)，等待Chrome启动，登陆；
    step 4 ：等待自动进入【包含目录的刷课页面】后，按enter；
    step 5 ：会展示 各章节的序号和标题 ，输入你想开始的序号，enter；
    step 6 ：自动播放并二倍速，完成后自动下一章节；
    step 7 ：随时可按 P 暂停，随后自主选择 跳转其他章节 or 继续播放。

    谢谢，祝各位好运！THANK U and GOOD LUCK!
'''
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from pynput import keyboard

# ==========================================
# 在这里直接填写你的课程 URL（选填）
# 如果填写了，脚本启动后将直接跳转；如果留空 ""，则运行后会询问。
# ==========================================
DEFAULT_URL = ""


is_paused = False
def on_press(key):
    global is_paused
    try:
        if hasattr(key, 'char') and key.char.lower() == 'p':
            is_paused = True
    except:
        pass


def convertTime(time_str):
    try:
        if not time_str or ':' not in time_str: return 0
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 2: return parts[0] * 60 + parts[1]
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except:
        return 0


def get_all_chapters(driver):

    selectors = [".posCatalog_select .posCatalog_name", ".onetoone a", ".leveltwo a"]
    for selector in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        if elements: return elements
    return []


def process_video_task(driver):

    global is_paused
    try:
        iframe1 = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'iframe')))
        driver.switch_to.frame(iframe1)
        video_iframes = driver.find_elements(By.CSS_SELECTOR, 'iframe[src*="/video/index.html"]')
        if not video_iframes: return

        for v_idx in range(len(video_iframes)):
            if is_paused: break
            driver.switch_to.default_content()
            driver.switch_to.frame(iframe1)
            v_frames = driver.find_elements(By.CSS_SELECTOR, 'iframe[src*="/video/index.html"]')
            driver.switch_to.frame(v_frames[v_idx])

            driver.execute_script(
                "var v=document.querySelector('video'); if(v){v.muted=true; v.playbackRate=2.0; v.play();}")

            try:
                duration_ele = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "vjs-duration-display")))
                total_s = convertTime(duration_ele.text)
                with tqdm(total=total_s, desc=f"    视频 {v_idx + 1}", unit="s", ncols=80, leave=False) as pbar:
                    last_s = 0
                    while not is_paused:
                        curr_s = driver.execute_script("return document.querySelector('video').currentTime;")
                        is_ended = driver.execute_script("return document.querySelector('video').ended;")
                        if curr_s is not None:
                            pbar.update(max(0, int(curr_s) - last_s))
                            last_s = int(curr_s)
                        if is_ended or (total_s > 0 and curr_s >= total_s - 1):
                            pbar.n = total_s
                            pbar.refresh()
                            break
                        driver.execute_script(
                            "var v=document.querySelector('video'); if(v.paused && !v.ended) v.play(); v.playbackRate=2.0;")
                        time.sleep(3)
            except:
                pass
    except:
        pass
    finally:
        driver.switch_to.default_content()


def main():
    global is_paused
    print("欢迎使用")
    # --- URL 处理逻辑 ---
    target_url = DEFAULT_URL.strip()
    if not target_url:
        print("\n" + "=" * 50)

        target_url = input(">>> 检测到内置 URL 为空，请在此粘贴你的课程 URL: [按enter确认]").strip()
        if not target_url:
            print("[错误] 未输入 URL，脚本退出。")
            return
    else:
        print(f"\n[系统] 使用代码内预设 URL: {target_url}")

    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(target_url)

    print("\n" + "=" * 60)
    print(" [操作指南] 按下键盘 [P] 键可随时暂停并手动跳转章节，按后请稍等。")
    print("=" * 60)
    input(">>> 请在浏览器完成登录并进入目录页后，[按 Enter] 开始初始化，按后请稍等。")

    chapters_elements = get_all_chapters(driver)
    total_len = len(chapters_elements)
    if total_len == 0:
        print("[错误] 未能识别到目录，请检查浏览器是否正确进入了目录页。")
        driver.quit();
        return

    print("\n" + "-" * 20 + " 目录编号预览 " + "-" * 20)
    for idx, chap in enumerate(chapters_elements):
        print(f"[{idx + 1}] {chap.text.strip()}")
    print("-" * 54)

    try:
        start_input = input(f"\n>>> 请输入起始章节编号 (1-{total_len}, 默认1): ").strip()
        current_idx = int(start_input) - 1 if start_input else 0
    except:
        current_idx = 0

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    while current_idx < total_len:

        if is_paused:
            listener.stop()
            print("\n" + "!" * 15 + " 脚本已手动暂停 " + "!" * 15)
            print(f" 当前进度: 第 {current_idx + 1} 节")
            print(" [1] 继续当前章节")
            print(" [2] 跳转到指定编号")
            print(" [3] 退出脚本")

            valid_cmd = False
            while not valid_cmd:
                choice = input(">>> 请选择操作 [1/2/3]: ").strip()
                if choice == '1':
                    valid_cmd = True
                elif choice == '2':
                    target_num = input(f">>> 请输入要跳转的编号 (1-{total_len}): ").strip()
                    try:
                        current_idx = int(target_num) - 1
                        valid_cmd = True
                        print(f"[系统] 准备跳转至编号: {target_num}")
                    except:
                        print("[错误] 输入无效数字！")
                elif choice == '3':
                    print("[系统] 正在关闭...");
                    driver.quit();
                    sys.exit()

            is_paused = False
            listener = keyboard.Listener(on_press=on_press)
            listener.start()
            print("[系统] 恢复运行...\n")
            time.sleep(1)

        chapters_elements = get_all_chapters(driver)
        if current_idx >= len(chapters_elements): break

        target = chapters_elements[current_idx]
        chapter_name = target.text.strip()

        if any(kw in chapter_name for kw in ["测验", "考试", "Quiz", "作业", "讨论"]):
            print(f"[跳过] 第 {current_idx + 1} 节: {chapter_name}")
            current_idx += 1
            continue

        print(f"\n[进行中] 第 {current_idx + 1}/{total_len} 节: {chapter_name}")

        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", target)

            # 等待内容加载
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'iframe')))
            time.sleep(2)

            process_video_task(driver)

            if not is_paused:
                current_idx += 1
        except Exception as e:
            print(f"    [警告] 状态异常: {e}")
            time.sleep(3)

    if listener.running: listener.stop()
    print("\n" + "=" * 60 + "\n>>> 任务全部完成，完结撒花！")
    input(">>> 按回车 [Enter] 退出脚本...")
    driver.quit()


if __name__ == "__main__":
    main()
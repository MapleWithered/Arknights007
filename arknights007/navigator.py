import os
import re
import time
import typing
from collections import namedtuple

from cnocr import CnOcr
from matplotlib import pyplot as plt

from adb import ADB
import cv2
import imgreco.imgops as imgops
import imgreco.template as template
import imgreco.ocr as ocr
import resource as res

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

StageInfo = namedtuple("StageInfo", ['info', 'stage_map'])
RectResult = namedtuple("RectResult", ['rect', 'val'])

OCRSingleResult = namedtuple("OCRSingleResult", ['str', 'val'])
OCRSTDSingleResult = namedtuple("OCRSTDSingleResult", ['str', 'rect', 'val'])


def press_std_pos(path):
    pos = Pos(*imgops.from_std_pos(ADB.get_resolution(), Pos(*res.get_pos(path))))
    ADB.input_press_pos(imgops.from_std_pos(ADB.get_resolution(), pos))
    time.sleep(1)


def press_std_rect(path):
    pos_rect = Rect(*imgops.from_std_rect(ADB.get_resolution(), Rect(*res.get_pos(path))))
    ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), pos_rect))
    time.sleep(1)


def swipe_std_pos(path_start, path_end, duration_ms):
    pos_start = Pos(*imgops.from_std_pos(ADB.get_resolution(), Pos(*res.get_pos(path_start))))
    pos_end = Pos(*imgops.from_std_pos(ADB.get_resolution(), Pos(*res.get_pos(path_end))))
    ADB.input_swipe_pos(pos_start, pos_end, duration_ms)


def is_main_menu():
    template_shortpath = "/main_menu/gear.png"
    img_gray = ADB.screencap_mat(gray=True)
    pos_rect = res.get_pos("/main_menu/gear")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    cropped = imgops.mat_pick_grey(cropped, 255)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    gear_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, gear_template) > 0.9:
        return True
    else:
        return False


def is_terminal():
    template_shortpath = "/terminal/terminal_template.png"
    img_gray = ADB.screencap_mat(gray=True)
    pos_rect = res.get_pos("/terminal/terminal_template")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    cropped = imgops.mat_pick_grey(cropped, 235, 20)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) > 0.9:
        return True
    else:
        return False


def is_battle_start_button_visible():
    template_shortpath = "/before_battle/start_button.png"
    img_gray = ADB.screencap_mat(gray=True)
    pos_rect = res.get_pos("/before_battle/start_button")
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) > 0.9:
        return True
    else:
        return False


# If not exist, return False.
# If succeed, return True.
def expand_menu_bar():
    template_shortpath = "/navigate_bar/nav_main.png"
    pos_shortpath = "/navigate_bar/nav_main"
    img = ADB.screencap_mat()
    img_gray = imgops.mat_bgr2gray(img)
    pos_rect = res.get_pos(pos_shortpath)
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    cropped = imgops.mat_pick_grey(cropped, 235, 20)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) > 0.9:
        return True

    template_shortpath = "/navigate_bar/nav_menu.png"
    pos_shortpath = "/navigate_bar/nav_menu"
    pos_rect = res.get_pos(pos_shortpath)
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) < 0.9:
        return False
    ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    time.sleep(0.8)
    return True


def menu_bar_press_main_menu():
    pos_shortpath = "/navigate_bar/nav_main"
    pos_rect = imgops.from_std_rect(ADB.get_resolution(), Rect(*res.get_pos(pos_shortpath)))
    ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    time.sleep(1)


def menu_bar_press_terminal():
    pos_shortpath = "/navigate_bar/nav_terminal"
    pos_rect = imgops.from_std_rect(ADB.get_resolution(), Rect(*res.get_pos(pos_shortpath)))
    ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    time.sleep(1)


def handle_back_button():
    template_shortpath = "/navigate_bar/back_black.png"
    pos_shortpath = "/navigate_bar/back_black"
    img = ADB.screencap_mat()
    img_gray = imgops.mat_bgr2gray(img)
    pos_rect = res.get_pos(pos_shortpath)
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    # cropped = imgops.mat_pick_grey(cropped, 235, 20)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) > 0.9:
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
        time.sleep(1)
        return True

    template_shortpath = "/navigate_bar/back_white.png"
    pos_shortpath = "/navigate_bar/back_white"
    pos_rect = res.get_pos(pos_shortpath)
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    # cropped = imgops.mat_pick_grey(cropped, 235, 20)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) > 0.9:
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
        time.sleep(1)
        return True

    return False


def handle_reward_scene():
    template_shortpath = "/reward_scene/reco_template.png"
    pos_shortpath = "/reward_scene/reco_template"
    pos_rect = res.get_pos(pos_shortpath)
    img = ADB.screencap_mat()
    img_gray = imgops.mat_bgr2gray(img)
    cropped = imgops.mat_crop(img_gray, imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
    cropped = imgops.mat_pick_grey(cropped, 130, 50)
    if not os.path.exists(res.get_img_path(template_shortpath)):
        cv2.imwrite(res.get_img_path(template_shortpath), cropped)
    terminal_template = res.get_img_gray(template_shortpath)
    if template.compare_mat(cropped, terminal_template) > 0.9:
        pos_shortpath = "/reward_scene/tick_button"
        pos_rect = res.get_pos(pos_shortpath)
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), Rect(*pos_rect)))
        time.sleep(1)
        return True
    else:
        return False


def handle_dialog():
    pass


def handle_unknown_scene():
    pass


def main_menu_press_terminal():
    press_std_rect("/main_menu/terminal")


def handle_close_button():
    # Use template match, find close button, mask needed.
    # https://gregorkovalcik.github.io/opencv_contrib/tutorial_template_matching.html

    template_shortpath = "/close_button/close_button.png"
    mask_shortpath = "/close_button/close_button_mask.png"

    img = ADB.screencap_mat(force=True, std_size=True)
    img_gray = imgops.mat_bgr2gray(img)
    img_gray = imgops.mat_pick_grey(img_gray, 89, 3)
    # cv2.imwrite("temp.png", img_gray)
    # plt.imshow(img_gray)

    img_template = res.get_img_gray(template_shortpath)
    img_mask = res.get_img_gray(mask_shortpath)

    result = template.match_masked_template_best(img_gray, img_template, img_mask)
    rect = result.rect
    val = result.val

    if val > 0.8:
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), rect))
        time.sleep(1)
        return True
    else:
        return False


# TODO: handle 正在提交至神经网络

def back_to_main_menu():
    error_counter = 0
    while not is_main_menu():
        if expand_menu_bar():
            menu_bar_press_main_menu()
            continue
        elif handle_back_button():
            continue
        elif handle_reward_scene():
            continue
        elif handle_dialog():
            continue
        elif handle_close_button():
            continue
        elif handle_unknown_scene():
            continue
        else:
            error_counter += 1
            time.sleep(1)
            if error_counter == 60:
                raise RuntimeError("Unhandled scene.")


def back_to_terminal():
    error_counter = 0
    while not is_terminal():
        if is_main_menu():
            main_menu_press_terminal()
        elif expand_menu_bar():
            menu_bar_press_terminal()
            continue
        elif handle_back_button():
            continue
        elif handle_reward_scene():
            continue
        elif handle_dialog():
            continue
        elif handle_close_button():
            continue
        elif handle_unknown_scene():
            continue
        else:
            error_counter += 1
            time.sleep(1)
            if error_counter == 60:
                raise RuntimeError("Unhandled scene.")


def _is_num_char(ch: str) -> bool:
    return len(ch) == 1 and '0' <= ch <= '9'


def stage_is_main_chapter(stage: str):
    parts = stage.split('-')
    part0 = parts[0]
    if _is_num_char(part0[-1]):  # '1-7', 'S4-1', etc
        return int(part0[-1])
    else:
        return None


def stage_is_resource(stage: str):
    parts = stage.split('-')
    part0 = parts[0]
    if part0 == 'LS':
        return 0
    if part0 in ('AP', 'SK', 'CE', 'CA'):
        return -1
    elif part0 == 'PR' and parts[1] in ('A', 'B', 'C', 'D'):
        return 1
    else:
        return None


def nav_terminal_to_main_story():
    press_std_pos("/terminal/main_story")


def nav_terminal_to_resource():
    press_std_pos("/terminal/resource")


def nav_main_story_choose_act(stage):
    act_table = [0, 0, 0, 0, 1, 1, 1, 1, 1, 2]
    target_act = act_table[stage_is_main_chapter(stage)]
    now_act = act_table[ocr.ocr_main_story_episode()]
    while now_act != target_act:
        if now_act > target_act:
            press_std_pos("/main_story/act_up")
        else:
            press_std_pos("/main_story/act_down")
        now_act = act_table[ocr.ocr_main_story_episode()]


def nav_main_story_choose_episode(stage):
    target_episode = stage_is_main_chapter(stage)
    now_episode = ocr.ocr_main_story_episode()
    while now_episode != target_episode:
        if now_episode > target_episode:
            swipe_std_pos("/main_story/episode_left", "/main_story/episode_now", 500)
        else:
            swipe_std_pos("/main_story/episode_now", "/main_story/episode_left", 500)
        now_episode = ocr.ocr_main_story_episode()
    press_std_pos("/main_story/episode_now")


def nav_main_story_choose_act_and_episode(stage: str):
    nav_main_story_choose_act(stage)
    nav_main_story_choose_episode(stage)


def nav_resource_choose_category(stage: str):
    region = stage_is_resource(stage)
    if region == 1:
        swipe_std_pos("/resources/swipe_middle", "/resources/swipe_left", 300)
    elif region == -1:
        swipe_std_pos("/resources/swipe_middle", "/resources/swipe_right", 300)

    parts = stage.split('-')
    part0 = '-'.join(parts[:-1])

    template_path = "/resources/" + part0 + ".png"

    img = ADB.screencap_mat(force=True, std_size=True)
    img_gray = imgops.mat_bgr2gray(img)

    img_template = res.get_img_gray(template_path)

    result = template.match_template_best(img_gray, img_template, cv2.TM_SQDIFF_NORMED)
    rect = result.rect
    val = result.val

    if val < 0.1:
        ADB.input_press_rect(imgops.from_std_rect(ADB.get_resolution(), rect))
        time.sleep(1)
        return True
    else:
        return False


def nav_get_stagemap_and_choose_stage_ocr(stage: str):
    ocr_dict = "0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    cn_ocr = CnOcr(cand_alphabet=ocr_dict)
    stage_map = res.get_stage_map_local(stage)
    if stage_map is None:
        stage_info = res.get_stage_info_full(stage)
        stage_map = stage_info.stage_map
    target_index = stage_map.index(stage)
    error_count = 0
    while error_count <= 10:
        ocrstd_result = ocr.ocr_all_stage_tag_and_std_position(stage_map, debug_show=False, cn_ocr_object=cn_ocr)
        visible_stage_index: list[int] = []
        for single_result in ocrstd_result:
            visible_stage_index.append(stage_map.index(single_result.str))
        if len(visible_stage_index) > 0:
            if target_index > max(visible_stage_index):
                ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(960, 540)),
                                    imgops.from_std_pos(ADB.get_resolution(), Pos(540, 540)),
                                    500)
                time.sleep(0.5)
            elif target_index < min(visible_stage_index):
                ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(960, 540)),
                                    imgops.from_std_pos(ADB.get_resolution(), Pos(1380, 540)),
                                    500)
                time.sleep(0.5)
            else:
                target_result = ocr.extract_result(stage, ocrstd_result)
                if target_result is not None:
                    ADB.input_press_rect(target_result.rect)
                    time.sleep(0.6)
                    if is_battle_start_button_visible():
                        return
                    else:
                        error_count += 1
                        time.sleep(1)
                else:
                    ADB.input_swipe_pos(imgops.from_std_pos(ADB.get_resolution(), Pos(960, 540)),
                                        imgops.from_std_pos(ADB.get_resolution(),
                                                            Pos(960 + 64 * (-1) ** error_count, 540)),
                                        500)
                    error_count += 1
                    time.sleep(2)
        else:
            error_count += 1
            time.sleep(2)
    raise RuntimeError("ocr找不到关卡")


def record_new(path: str):

    back_to_terminal()

    EVENT_LINE_RE = re.compile(r"(\S+): (\S+) (\S+) (\S+)$")
    records = []
    record_data = {
        'hw_ratio': res.get_img_path_suffix(),
        'records': records
    }
    print('滑动屏幕以退出录制.')
    print('开始录制, 请点击相关区域...')
    conn = ADB.create_connection()
    cmd = "shell:{}".format('getevent')
    conn.send(cmd)
    result = bytearray()
    while True:
        temp = conn.read(2147483647)
        if temp:
            result += temp
        else:
            break
    print(result)
    while True:
        x = 0
        y = 0
        point_list = []
        touch_down = False
        screen = self.adb.screenshot()
        while True:
            line = f.readline().decode('utf-8', 'replace').strip()
            # print(line)
            match = EVENT_LINE_RE.match(line.strip())
            if match is not None:
                dev, etype, ecode, data = match.groups()
                if '/dev/input/event5' != dev:
                    continue
                etype, ecode, data = int(etype, 16), int(ecode, 16), int(data, 16)
                # print(dev, etype, ecode, data)

                if (etype, ecode) == (1, 330):
                    touch_down = (data == 1)

                if touch_down:
                    if 53 == ecode:
                        x = data
                    elif 54 == ecode:
                        y = data
                    elif (etype, ecode, data) == (0, 0, 0):
                        # print(f'point: ({x}, {y})')
                        point_list.append((x, y))
                elif (etype, ecode, data) == (0, 0, 0):
                    break
        logger.debug(f'point_list: {point_list}')
        if len(point_list) == 1:
            point = point_list[0]
            x1 = max(0, point[0] - half_roi)
            x2 = min(self.viewport[0] - 1, point[0] + half_roi)
            y1 = max(0, point[1] - half_roi)
            y2 = min(self.viewport[1] - 1, point[1] + half_roi)
            roi = screen.crop((x1, y1, x2, y2))
            step = len(records)
            roi.save(os.path.join(record_dir, f'step{step}.png'))
            record = {'point': point, 'img': f'step{step}.png', 'type': 'tap',
                      'wait_seconds_after_touch': wait_seconds_after_touch,
                      'threshold': threshold, 'repeat': 1, 'raise_exception': True}
            logger.info(f'record: {record}')
            records.append(record)
            if wait_seconds_after_touch:
                logger.info(f'请等待 {wait_seconds_after_touch}s...')
                self.__wait(wait_seconds_after_touch)

            logger.info('继续...')
        elif len(point_list) > 1:
            # 滑动时跳出循环
            c = input('是否退出录制[Y/n]:')
            if c.strip().lower() != 'n':
                logger.info('停止录制...')
                break
            else:
                # todo 处理屏幕滑动
                continue
    with open(os.path.join(record_dir, f'record.json'), 'w', encoding='utf-8') as f:
        json.dump(record_data, f, ensure_ascii=False, indent=4, sort_keys=True)

def goto_special_stage(stage: str, allow_new_record=False):
    def goto_stage_special_record(stage_name, config=None):
        back_to_terminal()

        # 得到关卡前缀
        last_char_index = len(stage) - 1
        for i in range(len(stage))[::-1]:
            if not _is_num_char(stage[i]):
                last_char_index = i
                break
        stage_category = stage[:last_char_index + 1]
        if stage_category[-1] == '-':
            stage_category = stage_category[:-1]

        path = res.get_img_path('/special_stage_record/'+stage_category+'.yaml')
        if not os.path.exists(path):
            if allow_new_record:
                print('开始录制 ' + stage_category)
                record_new(path)
            else:
                return -1
        else:
            record_play(path)



    pass


def goto_stage(stage: str):
    back_to_terminal()
    if stage_is_main_chapter(stage) is not None:
        nav_terminal_to_main_story()
        nav_main_story_choose_act_and_episode(stage)
    elif stage_is_resource(stage) is not None:
        nav_terminal_to_resource()
        if nav_resource_choose_category(stage) is False:
            raise RuntimeError("日替资源关卡未开放")
    else:
        goto_special_stage(stage)
        raise RuntimeError("TODO: 操作录制")
    time.sleep(0.5)
    nav_get_stagemap_and_choose_stage_ocr(stage)
    time.sleep(1)






if __name__ == '__main__':
    record_new('1-7')
    pass

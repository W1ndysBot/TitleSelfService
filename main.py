# script/TitleSelfService/main.py

import logging
import os
import sys
import re
import json

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import *
from app.api import *
from app.switch import load_switch, save_switch


# 数据存储路径，实际开发时，请将TitleSelfService替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "TitleSelfService",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "TitleSelfService")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "TitleSelfService", status)


# 处理元事件，用于启动时确保数据目录存在
async def handle_TitleSelfService_meta_event(websocket):
    os.makedirs(DATA_DIR, exist_ok=True)


# 处理开关状态
async def toggle_function_status(websocket, group_id, message_id, authorized):
    if not authorized:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌你没有权限对TitleSelfService功能进行操作,请联系管理员。",
        )
        return

    if load_function_status(group_id):
        save_function_status(group_id, False)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]🚫🚫🚫TitleSelfService功能已关闭",
        )
    else:
        save_function_status(group_id, True)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]✅✅✅TitleSelfService功能已开启",
        )


async def SetTitleSelfService(websocket, group_id, user_id, message_id, raw_message):
    """
    自助设置头衔
    """
    try:
        match = re.match(r"给我头衔(.*)", raw_message)
        if match:
            title = match.group(1)
            await set_group_special_title(
                websocket,
                group_id,
                user_id,
                title,
            )
            # await send_group_msg(
            #     websocket,
            #     group_id,
            #     f"[CQ:reply,id={message_id}]✅✅✅已设置头衔为 {title}",
            # )
    except Exception as e:
        logging.error(f"自助设置头衔失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "自助设置头衔失败，错误信息：" + str(e),
        )
        return


async def handle_TitleSelfService_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))
        authorized = user_id in owner_id

        # 开关
        if raw_message == "tss":
            await toggle_function_status(websocket, group_id, message_id, authorized)
            return
        # 检查是否开启
        if load_function_status(group_id):
            # 设置头衔
            await SetTitleSelfService(
                websocket, group_id, user_id, message_id, raw_message
            )
    except Exception as e:
        logging.error(f"处理TitleSelfService群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理TitleSelfService群消息失败，错误信息：" + str(e),
        )
        return


# 群通知处理函数
async def handle_TitleSelfService_group_notice(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))

    except Exception as e:
        logging.error(f"处理TitleSelfService群通知失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理TitleSelfService群通知失败，错误信息：" + str(e),
        )
        return


# 回应事件处理函数
async def handle_TitleSelfService_response_message(websocket, message):
    try:
        msg = json.loads(message)

        if msg.get("status") == "ok":
            echo = msg.get("echo")

            if echo and echo.startswith("xxx"):
                pass
    except Exception as e:
        logging.error(f"处理TitleSelfService回应事件时发生错误: {e}")


# 统一事件处理入口
async def handle_events(websocket, msg):
    """统一事件处理入口"""
    try:
        # 处理回调事件
        if msg.get("status") == "ok":
            await handle_TitleSelfService_response_message(websocket, msg)
            return

        post_type = msg.get("post_type")

        # 处理元事件
        if post_type == "meta_event":
            await handle_TitleSelfService_meta_event(websocket)

        # 处理消息事件
        elif post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await handle_TitleSelfService_group_message(websocket, msg)
            elif message_type == "private":
                return

        # 处理通知事件
        elif post_type == "notice":
            if msg.get("notice_type") == "group":
                await handle_TitleSelfService_group_notice(websocket, msg)

    except Exception as e:
        error_type = {
            "message": "消息",
            "notice": "通知",
            "request": "请求",
            "meta_event": "元事件",
        }.get(post_type, "未知")

        logging.error(f"处理TitleSelfService{error_type}事件失败: {e}")

        # 发送错误提示
        if post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await send_group_msg(
                    websocket,
                    msg.get("group_id"),
                    f"处理TitleSelfService{error_type}事件失败，错误信息：{str(e)}",
                )
            elif message_type == "private":
                await send_private_msg(
                    websocket,
                    msg.get("user_id"),
                    f"处理TitleSelfService{error_type}事件失败，错误信息：{str(e)}",
                )

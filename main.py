import flet as ft
import aiohttp
from loguru import logger
import requests
from datetime import datetime
import rtoml


logger.add("logs/latest.log", level="DEBUG")

with open("data/config.toml", "r") as f:
    config = rtoml.loads(f.read())

API_URL = config["common"]["api"]

count_need_review = 0
count_total = 0
reviewed = []

def format_datetime(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str

def rewind(number: int):
    try:
        with open("data/rewind.txt","w") as f:
            f.write(str(number))
            with requests.post(API_URL+"reset", timeout=10) as resp:
                resp.raise_for_status()
            with requests.post(API_URL+"rewind?n="+str(number), timeout=10) as resp:
                resp.raise_for_status()
                logger.info("Rewind "+str(number))
                
    except Exception as e:
        logger.error(f"Rewind failed: {e}")

async def fetch_patches():
    try:
        while 1:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL+"latest") as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    logger.trace(data.get("data", {}).get("entries", []))
                    logger.trace(data)
                    if data.get("data", {}).get("entries", []) != []:
                        return data.get("data", {}).get("entries", [])
    except Exception as e:
        logger.error(f"Get email list failed: {e}")
        return []

def main(page: ft.Page):
    page.title = "KDocReview"
    page.scroll = "adaptive"
    page.theme_mode = "light"
    page.padding = 10
    page.window_width = 1200
    page.window_height = 800

    # 顶部统计卡片
    stats_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EMAIL, color=ft.Colors.BLUE, size=24),
                    ft.Text("邮件统计", size=18, weight=ft.FontWeight.BOLD)
                ]),
                ft.Divider(height=1, thickness=1),
                ft.Row([
                    ft.Column([
                        ft.Text("总邮件数", size=12, color=ft.Colors.GREY_600),
                        ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE, data="total_count")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(width=30),
                    ft.Column([
                        ft.Text("待审核", size=12, color=ft.Colors.GREY_600),
                        ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED, data="need_review_count")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(width=30),
                    ft.Column([
                        ft.Text("已审核", size=12, color=ft.Colors.GREY_600),
                        ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN, data="reviewed_count")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
            ], spacing=8),
            padding=15,
            border_radius=10,
        )
    )

    patch_list = ft.ListView(expand=True, spacing=8, padding=10)
    status_text = ft.Text("点击刷新按钮加载邮件列表", color=ft.Colors.GREY_500, size=14)

    async def refresh_patches():
        # 显示加载状态
        status_text.value = "正在加载邮件列表..."
        status_text.color = ft.Colors.BLUE
        page.update()

        entries = await fetch_patches()
        global count_total
        count_total += len(entries)
        global count_need_review
        
        new_entries_count = 0
        for entry in entries:
            subject = entry.get("subject", "无主题")
            author = entry.get("author", "未知")
            email = entry.get("email", "")
            url = entry.get("url", "#")
            received_at = entry.get("received_at", "")
            subsystem = entry.get("subsystem", "unknown")
            summary = entry.get("summary", "")

            if subject not in reviewed:
                count_need_review += 1
                bg_color = ft.Colors.BLUE_50
                badge = ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.REMOVE_RED_EYE, size=14, color=ft.Colors.WHITE),
                        ft.Text("待审核", size=12, color=ft.Colors.WHITE)
                    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.RED,
                    border_radius=16,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                )
                new_entries_count += 1
            else:
                bg_color = ft.Colors.GREY_100
                badge = ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=ft.Colors.WHITE),
                        ft.Text("已审核", size=12, color=ft.Colors.WHITE)
                    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.GREEN,
                    border_radius=16,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                )

            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text(subject, weight=ft.FontWeight.BOLD, size=14, 
                                       spans=[ft.TextSpan(
                                           subject,
                                           style=ft.TextStyle(decoration=ft.TextDecoration.NONE)
                                       )])
                            ], expand=True),
                            badge,
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=1, color=ft.Colors.GREY_200),
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, size=16, color=ft.Colors.GREY_600),
                            ft.Text(f"{author}", size=12, color=ft.Colors.GREY_600),
                            ft.Icon(ft.Icons.EMAIL, size=16, color=ft.Colors.GREY_600),
                            ft.Text(f"{email}", size=12, color=ft.Colors.GREY_600),
                            ft.Icon(ft.Icons.INFO, size=16, color=ft.Colors.GREY_600),
                            ft.Text(f"{subsystem}", size=12, color=ft.Colors.GREY_600),
                        ], spacing=8),
                        ft.Row([
                            ft.Icon(ft.Icons.ACCESS_TIME, size=14, color=ft.Colors.GREY_500),
                            ft.Text(f"{format_datetime(received_at)}", size=11, color=ft.Colors.GREY_500),
                        ], spacing=4),
                        ft.Divider(height=1, color=ft.Colors.GREY_200),
                        ft.Row([
                            ft.FilledButton(
                                "标记已审",
                                icon=ft.Icons.CHECK,
                                on_click=lambda e, s=subject: mark_as_reviewed(s),
                                style=ft.ButtonStyle(
                                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                                    elevation=1,
                                )
                            )
                        ], spacing=8)
                    ], spacing=8),
                    padding=15,
                    bgcolor=bg_color,
                    border_radius=12,
                    border=ft.Border.all(1, ft.Colors.GREY_200),
                    data=url,
                )
            )
            patch_list.controls.append(card)

        # 更新统计数据
        reviewed_count = count_total - count_need_review
        stats_card.content.content.controls[2].controls[0].controls[1].value = str(count_total)
        stats_card.content.content.controls[2].controls[2].controls[1].value = str(count_need_review)
        stats_card.content.content.controls[2].controls[4].controls[1].value = str(reviewed_count)
        
        status_text.value = f"共 {count_total} 封邮件，其中 {count_need_review} 封需要审核，新增 {new_entries_count} 封"
        status_text.color = ft.Colors.GREEN if new_entries_count > 0 else ft.Colors.GREY_600
        page.update()

    def mark_as_reviewed(subject):
        """标记邮件为已审核"""
        if subject not in reviewed:
            reviewed.append(subject)
            global count_need_review
            count_need_review -= 1
            
            # 更新统计
            reviewed_count = count_total - count_need_review
            stats_card.content.content.controls[2].controls[0].controls[1].value = str(count_total)
            stats_card.content.content.controls[2].controls[2].controls[1].value = str(count_need_review)
            stats_card.content.content.controls[2].controls[4].controls[1].value = str(reviewed_count)
            
            status_text.value = f"已标记邮件为已审核 - 剩余 {count_need_review} 封待审核"
            status_text.color = ft.Colors.BLUE
            page.update()

    def handle_refresh_click(e: ft.Event[ft.Button]):
        number = int(rewind_button.value) if rewind_button.value.isdigit() else 500
        rewind(number)
        page.run_task(refresh_patches)

    def handle_clear_all(e):
        """清空所有邮件列表"""
        patch_list.controls.clear()
        global count_total, count_need_review
        count_total = 0
        count_need_review = 0
        reviewed.clear()
        
        stats_card.content.content.controls[2].controls[0].controls[1].value = "0"
        stats_card.content.content.controls[2].controls[2].controls[1].value = "0"
        stats_card.content.content.controls[2].controls[4].controls[1].value = "0"
        
        status_text.value = "已清空所有邮件列表"
        status_text.color = ft.Colors.GREY_500
        page.update()

    try:
        with open("data/rewind.txt","r") as f:
            rewind_num = f.read()
            if rewind_num == "":
                rewind_num = 500
    except FileNotFoundError:
        rewind_num = 500

    # 控制面板
    control_panel = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("控制面板", size=16, weight=ft.FontWeight.BOLD),
                ]),
                ft.Divider(height=1, thickness=1),
                ft.Row([
                    rewind_button := ft.TextField(
                        label="加载邮件数量", 
                        value=str(rewind_num), 
                        width=150,
                        keyboard_type=ft.KeyboardType.NUMBER,
                        suffix_icon=ft.Icons.NUMBERS
                    ),
                    ft.FilledButton(
                        "刷新列表",
                        on_click=handle_refresh_click,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE
                        )
                    ),
                    ft.OutlinedButton(
                        "清空列表",
                        icon="clear",
                        on_click=handle_clear_all,
                        style=ft.ButtonStyle(
                            color=ft.Colors.RED
                        )
                    ),
                    ft.Text("提示：调整数字后点击刷新来重新获取指定数量的邮件", 
                           size=12, color=ft.Colors.GREY_600, expand=True),
                    ft.FilledButton(
                        "下一页",
                        on_click=page.run_task(refresh_patches),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE
                        )
                    ),
                ], alignment=ft.MainAxisAlignment.START, spacing=10),
            ], spacing=10),
            padding=15,
            border_radius=10,
        )
    )

    page.add(
        ft.AppBar(
            title=ft.Row([
                ft.Icon(ft.Icons.CODE, color=ft.Colors.BLUE),
                ft.Text("KDocReview", weight=ft.FontWeight.BOLD)
            ], spacing=10),
            bgcolor=ft.Colors.BLUE_50,
            color=ft.Colors.BLUE,
            elevation=2,
        ),
        ft.Column([
            stats_card,
            control_panel,
            ft.Row([status_text], spacing=10),
            ft.Divider(height=1, thickness=1),
            patch_list,
        ], expand=True, spacing=10)
    )

if __name__ == "__main__":
    ft.run(main)

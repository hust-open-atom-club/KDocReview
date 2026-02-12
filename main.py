import flet as ft
import aiohttp
from datetime import datetime

API_URL = "http://127.0.0.1:8000/"

count_need_review = 0
count_total = 0
reviewed = []

def format_datetime(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str

async def rewind(number):
    try:
        with open("data/rewind.txt","w") as f:
            f.write(number)
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL+"reset", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                data = await resp.json()
            async with session.post(API_URL+"rewind?n="+str(number), timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                data = await resp.json()
                print("[INFO] Rewind "+str(number))
                return data.get("data", {}).get("entries", [])
    except Exception as e:
        print(f"[ERROR] Rewind failed: {e}")
        return []
    
async def fetch_patches():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL+"latest") as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", {}).get("entries", [])
    except Exception as e:
        print(f"[ERROR] Get email list failed: {e}")
        return []

def main(page: ft.Page):
    page.title = "KDocReview"
    page.scroll = "auto"
    page.theme_mode = "light"

    patch_list = ft.ListView(expand=True, spacing=12, padding=10)
    status_text = ft.Text("点击刷新加载邮件", color=ft.Colors.GREY)

    async def refresh_patches():
        entries = await fetch_patches()
        global count_total
        count_total += len(entries)
        global count_need_review
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
                    ft.Text("Need Review", size=12, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.RED,
                    border_radius=4,
                    padding=4,
                )
            else:
                bg_color = ft.Colors.GREY_100
                badge = ft.Container(
                    ft.Text("Reviewed", size=12, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.GREEN,
                    border_radius=4,
                    padding=4,
                )

            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(subject, weight="bold", expand=True),
                            badge,
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"{author} <{email}>", size=13, color=ft.Colors.GREY_700),
                        ft.Text(f"subsystem: {subsystem} | {format_datetime(received_at)}", size=12, color=ft.Colors.GREY_600),
                        ft.Text(summary, size=13, color=ft.Colors.BLACK),
                    ], spacing=4),
                    padding=12,
                    bgcolor=bg_color,
                    border_radius=8,
                    data=url,
                )
            )
            patch_list.controls.append(card)

        status_text.value = f"共 {count_total} 封邮件，其中 {count_need_review} 封需要审核"
        status_text.color = ft.Colors.BLACK
        page.update()

    try:
        with open("data/rewind.txt","r") as f:
            rewind_num = f.read()
    except FileNotFoundError:
        rewind_num = 500
    
    def handle_refresh_click(e: ft.Event[ft.Button]):
        rewind(rewind_button.value)
        page.run_task(refresh_patches)

    page.add(
        ft.AppBar(
            title=ft.Text("KDocReview"),
            bgcolor=ft.Colors.WHITE,
        ),
        ft.Button("刷新", icon="refresh", on_click=handle_refresh_click),
        rewind_button := ft.TextField(label="邮件数量", value=rewind_num),
        status_text,
        patch_list,
    )

    rewind(rewind_num)
    page.run_task(refresh_patches)

if __name__ == "__main__":
    ft.run(main)
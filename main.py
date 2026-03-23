import flet as ft

def main(page: ft.Page):
    page.title = "FB2 Audiobook Maker"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    text_field = ft.Text("Приложение готово к работе!", size=20)
    
    page.add(
        ft.Container(
            content=ft.Column([
                text_field,
                ft.ElevatedButton("Проверить кнопку", on_click=lambda e: print("Работает!"))
            ]),
            padding=20
        )
    )

ft.app(target=main)

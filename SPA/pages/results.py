import reflex as rx
import os
import asyncio
import time
from reflex.components.radix.themes.base import (
    LiteralAccentColor,
)


# ──────────────────────────────────────────────────────────────
# App Theme Configuration
# ──────────────────────────────────────────────────────────────
theme = rx.theme(
    appearance="light",
    accent_color="orange",
    radius="large",
    font="system",
)

# ──────────────────────────────────────────────────────────────
# Constants for File Handling
# ──────────────────────────────────────────────────────────────
FILE_PATH = "Output/llm.txt"
DEFAULT_CONTENT = "⚠️ Output file not found."

# ──────────────────────────────────────────────────────────────
# State Management for the Result Page
# ──────────────────────────────────────────────────────────────
class ResultState(rx.State):
    content: str = DEFAULT_CONTENT
    is_loading: bool = False

    @rx.event
    def load_content(self):
        self.is_loading = True


        if os.path.exists(FILE_PATH):
            try:
                with open(FILE_PATH, "r", encoding="utf-8") as f:
                    self.content = f.read()
                    print("✅ Loaded content length:", len(self.content))
            except Exception as e:
                print("❌ Error reading file:", e)
                self.content = DEFAULT_CONTENT
        else:
            print(f"❌ FILE NOT FOUND: {FILE_PATH}")
            self.content = DEFAULT_CONTENT

        self.is_loading = False
# ──────────────────────────────────────────────────────────────
# UI Components
# ──────────────────────────────────────────────────────────────
@rx.page(route="/results", on_load=ResultState.load_content)
def result_page():
    return rx.container(
        rx.fragment(
            # 🔹 Grainy Background Overlay
            rx.box(
                style={
                    "position": "absolute",
                    "top": 0,
                    "left": 0,
                    "width": "100%",
                    "height": "100%",
                    "backgroundImage": "url('https://grainy-gradients.vercel.app/noise.svg')",
                    "opacity": 0.4,
                    "zIndex": -2,
                    "pointerEvents": "none",
                }
            ),

            # 🔹 Heading Section
            rx.vstack(
                rx.text("LLM.TXT", size="9", weight="bold", color="#1e1e1d", text_align="center"),
                rx.text("for AI & agents", size="8", weight="bold", color="#e78642", text_align="center"),
                spacing="1",
                align="center",
                style={"paddingTop": "2.2rem"},
            ),
            

            rx.grid(
                
                rx.card(
                    rx.flex(
                        rx.box(
                            rx.hstack(  # Icon and Heading side by side
                                rx.icon("file-text"),
                                rx.heading("3,300"),
                                spacing="2",
                                align="center",
                            ),
                           # rx.heading("Token Count"),
                            rx.box(height="0.5rem"),
                            rx.text("Total tokens size extracted from this website")

                        ),
                        direction="column",
                        spacing="4",
                    ),
                    as_child=True,
                    style={"marginTop": "1.5rem"},
                ),

                
                rx.card(
                    rx.flex(
                        rx.box(
                            rx.hstack(  # Icon and Heading side by side
                                rx.icon("database"),
                                rx.heading("3,300"),
                                spacing="2",
                                align="center",
                            ),
                          #  rx.heading("Docs"),
                            rx.box(height="0.5rem"),  
                            rx.text("Compressed file size ready for AI usage")
,
                        ),
                        spacing="2",
                    ),
                    as_child=True,
                    style={"marginTop": "1.5rem"},
                ),
                rx.card(
                    rx.flex(
                        rx.box(
                            rx.hstack(  # Icon and Heading side by side
                                rx.icon("dollar-sign"),
                                rx.heading("3,300"),
                                spacing="2",
                                align="center",
                            ),
                           # rx.heading("Estimated Cost"),
                            rx.box(height="0.5rem"),
                            rx.text("Approximate cost for using this with an LLM")
,
                        ),
                        spacing="2",
                    ),
                    as_child=True,
                    style={"marginTop": "1.5rem"},
                ),
                
                rx.card(
                    rx.flex(
                        rx.box(
                            rx.hstack(  # Icon and Heading side by side
                                rx.icon("Clock"),
                                rx.heading("3,300"),
                                spacing="2",
                                align="center",
                            ),
                           # rx.heading("Time Taken"),
                            rx.box(height="0.5rem"),
                            rx.text("Time taken to analyze this website"),
                        ),
                        spacing="2",
                    ),
                    as_child=True,
                    style={"marginTop": "1.5rem"},
                ),
                
                
                
                columns="2",
                spacing="4",
                width="100%",
                style={"alignItems": "stretch"},
            ),
            
            # 🔹 Main Output Box
            rx.box(
                rx.box(
                    # 🔹 Action Buttons (Copy + Download)
                    rx.hstack(
                        rx.button(
                            rx.icon(tag="copy"),
                            on_click=[
                                rx.set_clipboard(ResultState.content),
                                rx.toast(
                                    rx.hstack(
                                        rx.icon(tag="circle_check"),
                                        rx.text("Copied to clipboard"),
                                    ),
                                    duration=60000,
                                    style={
                                        "text-align": "left",
                                        "border": "0.5px solid #4CAF50",
                                        "backgroundColor": "rgb(124 200 144 / 12%) !important",
                                        "color": "green",
                                    },
                                ),
                            ],
                            variant="soft",
                            color_scheme="gray",
                            size="1",
                            title="Copy to clipboard",
                            aria_label="Copy content to clipboard",
                            style={
                                "backgroundColor": "transparent",
                            },
                            _hover={
                                "backgroundColor": "rgba(128, 128, 128, 0.15)",
                                "cursor": "pointer",
                            },
                        ),
                        rx.button(
                            rx.icon(tag="download"),
                            on_click=rx.download(
                                data=ResultState.content,
                                filename="llm.txt",
                            ),
                            variant="soft",
                            color_scheme="gray",
                            size="1",
                            title="Download content",
                            aria_label="Download content",
                            style={
                                "backgroundColor": "transparent",
                            },
                            _hover={
                                "backgroundColor": "rgba(128, 128, 128, 0.15)",
                                "cursor": "pointer",
                            },
                        ),
                        spacing="2",
                        style={
                            "position": "absolute",
                            "top": "1.5rem",
                            "right": "0.5rem",
                            "zIndex": 10,
                        },
                    ),

                    # 🔹 Scrollable Code Block Area
                    rx.scroll_area(
                        rx.code_block(
                            ResultState.content,
                            language="markdown",
                            show_line_numbers=True,
                        ),
                        style={
                            "height": "45vh",
                            "width": "100%",
                            "maxWidth": "1200px",
                            "padding": "3.5rem 1.1rem 0.2rem 1.1rem",
                            "marginTop": "1rem",
                            "borderRadius": "12px",
                            "background": "#fafafa",
                            "overflowX": "auto",
                            "position": "relative",
                        },
                    ),
                    style={
                        "position": "relative",
                        "width": "100%",
                        "maxWidth": "95vw",
                        "margin": "1rem auto",
                    },
                ),
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "width": "100%",
                },
            ),
        ),
        style={
            "background": "linear-gradient(to right, #ffffff, #e4b38d5c)",
            "height": "auto",
            "padding": 0,
            "backdropFilter": "blur(4px)",
            "-webkit-backdrop-filter": "blur(4px)",
        },
    )

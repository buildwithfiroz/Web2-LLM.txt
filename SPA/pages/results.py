import reflex as rx
import aiofiles
from reflex.components.radix.themes.base import (
    LiteralAccentColor,
)
import tiktoken
import os
import requests
import time
from millify import millify
from ..components import loader  


now = time.time()
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
# Constants
# ──────────────────────────────────────────────────────────────
FILE_PATH = "Output/llm.txt"
DEFAULT_CONTENT = "⚠️ Output file not found."

USD_COST_PER_1K_TOKENS = 0.01
INR_CACHE_DURATION = 60 * 60
INR_FALLBACK_RATE = 83.0
CURRENCY_API_TIMEOUT = 0.3

_encoding = tiktoken.get_encoding("cl100k_base")
_cached_inr_rate = INR_FALLBACK_RATE
_last_inr_fetch = 0


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{round(seconds, 2)} sec"
    minutes = int(seconds // 60)
    remaining = round(seconds % 60, 1)
    if remaining == 0:
        return f"{minutes} min"
    return f"{minutes} min {remaining} sec"


# ──────────────────────────────────────────────────────────────
# Helper Functions (place this here)
# ──────────────────────────────────────────────────────────────

def get_cached_inr_rate():
    global _cached_inr_rate, _last_inr_fetch
    

    if now - _last_inr_fetch < INR_CACHE_DURATION:
        return _cached_inr_rate

    try:
        response = requests.get(
            "https://api.exchangerate.host/convert?from=USD&to=INR",
            timeout=CURRENCY_API_TIMEOUT
        )
        data = response.json()
        _cached_inr_rate = data.get("result", INR_FALLBACK_RATE)
        _last_inr_fetch = now
    except:
        _cached_inr_rate = INR_FALLBACK_RATE

    return _cached_inr_rate

def analyze_llm_file(file_path: str) -> dict:
    now = time.time()  # ⛳ Start timing

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    token_count = len(_encoding.encode(content))
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / 1024 / 1024
    usd_cost = (token_count / 1000) * USD_COST_PER_1K_TOKENS
    inr_cost = usd_cost * get_cached_inr_rate()

    end_time = time.time()
    analysis_duration_sec = round(end_time - now, 2)

    return {
        "tokens": millify(token_count, precision=2),
        "inr_cost": f"{millify(inr_cost, precision=2)}",
        "file_size_mb": round(file_size_mb, 2),
        "time_spent": analysis_duration_sec,  # 🟢 Fix the key name
    }


# ──────────────────────────────────────────────────────────────
# State Management for the Result Page
# ──────────────────────────────────────────────────────────────
class ResultState(rx.State):
    # === Content and Loader ===
    content: str = DEFAULT_CONTENT
    is_loading: bool = False
    elapsed_time: float = 0.0  # to store time taken in seconds
    # === Card data fields (must be declared before usage) ===
    tokens: str = "0"  # Change from int to str
    file_size_mb: float = 0.0
    inr_cost: str = "0"  # Change from float to str
    # NEW: For tracking time taken
    analysis_time: float = 0.0
    analysis_time_readable: str = "0s"

    @rx.event
    async def load_content(self):
        self.is_loading = True
        if os.path.exists(FILE_PATH):
            async with aiofiles.open(FILE_PATH, "r", encoding="utf-8") as f:
                self.content = await f.read()
            stats = analyze_llm_file(FILE_PATH)
            self.tokens = stats["tokens"]  # Already a string (e.g., "1.25k")
            self.file_size_mb = stats["file_size_mb"]
            self.inr_cost = stats["inr_cost"]  # Already a string (e.g., "1.04")
            self.analysis_time = stats["time_spent"]
            # Format readable time
            if self.analysis_time < 60:
                self.analysis_time_readable = f"{self.analysis_time:.2f}s"
            else:
                self.analysis_time_readable = f"{self.analysis_time / 60:.2f} min"
        else:
            self.content = DEFAULT_CONTENT
            print("Content not found. Using default content.")
        self.is_loading = False



# ──────────────────────────────────────────────────────────────
# UI Components
# ──────────────────────────────────────────────────────────────
@rx.page(route="/results", on_load=ResultState.load_content)
def result_page():
    return rx.container(
        rx.fragment(
            rx.cond(
                ResultState.is_loading,  # Show loader while loading
                loader(ResultState.is_loading),  # Use the reusable loader
            ),
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
                                rx.heading(ResultState.tokens),
                                spacing="2",
                                align="center",
                            ),
                           # rx.heading("Token Count"),
                            rx.box(height="0.7rem"),
                            rx.text("Estimated tokens size extracted ")

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
                                rx.heading(f"{ResultState.file_size_mb:.2f} MB"),
                                spacing="2",
                                align="center",
                            ),
                          #  rx.heading("Docs"),
                            rx.box(height="0.7rem"),  
                            rx.text("Optimized File Size for Training")
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
                                rx.icon("wallet-minimal"),
                                rx.heading(f"₹{ResultState.inr_cost:.2f}"),
                                spacing="2",
                                align="center",
                            ),
                           # rx.heading("Estimated Cost"),
                            rx.box(height="0.7rem"),
                            rx.text("Approximate Embedding Cost ")
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
                                rx.heading(ResultState.analysis_time_readable),
                                spacing="2",
                                align="center",
                            ),
                           # rx.heading("Time Taken"),
                            rx.box(height="0.7rem"),
                            rx.text("Time taken to analyze"),
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
                        rx.tooltip(
                            rx.button(
                                rx.icon(tag="copy",style={'width':'80%'}),
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
                            content='Copy llm context',
                        ),
                        rx.tooltip(
                            rx.button(
                                rx.icon(tag="download",style={'width':'80%'}),
                                on_click=rx.download(
                                    data=open(FILE_PATH, "r").read() if os.path.exists(FILE_PATH) else "File not found.",
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
                                is_disabled=ResultState.is_loading,
                            ),
                            
                            content="Download Your Llm File",
                        ),
                        spacing="0",
                        style={
                            "position": "absolute",
                            "top": "1.5rem",
                            "right": "0.7rem",
                            "zIndex": 10,
                        },
                    ),

                    # 🔹 Scrollable Code Block Area
                    
                    
                    rx.scroll_area(
                        rx.cond(
                            ResultState.content != "",
                            rx.code_block(
                                ResultState.content,
                                language="markdown",
                                show_line_numbers=True,
                                
                                style={
                                    "background": "transparent !important",
                                    "backgroundColor": "transparent",
                                },
                                
                            ),
                        
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


#app = rx.App(theme=theme, stylesheets="/styles.css",)
app = rx.App(
    theme=theme,
    stylesheets=[
        "/styles.css",  # This path is relative to assets/
    ],
)

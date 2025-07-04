import reflex as rx
from rxconfig import config
from .pages.results import result_page
from state import main  # Your LLM processing function
import re
import httpx
import uuid
from database import save_user_url, create_table

# ──────────────────────────────────────────────────────────────
#  Make sure table exists on app start
# ──────────────────────────────────────────────────────────────
create_table()

# ──────────────────────────────────────────────────────────────
# ✅ Helper function to check if URL is reachable
# ──────────────────────────────────────────────────────────────
async def check_url_reachable(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(url, follow_redirects=True)
            return response.status_code == 200
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────
# ✅ State for toggle (single page vs whole site)
# ──────────────────────────────────────────────────────────────
class SwitchState(rx.State):
    value: bool = False
    show_modal: bool = False

    @rx.var
    def mode_text(self) -> str:
        return "Whole Website" if self.value else "Single Webpage"

    @rx.event
    def set_end(self, value: bool):
        self.value = value
        if value:
            self.show_modal = True

    @rx.event
    def close_modal(self):
        self.value = False
        self.show_modal = False


# ──────────────────────────────────────────────────────────────
# ✅ Main App State
# ──────────────────────────────────────────────────────────────
class State(rx.State):
    input_text: str = ""
    is_loading: bool = False
    show_loader: bool = False 
    show_alert: bool = False
    alert_message: str = ""
    user_id: str = ""
    
    # @rx.event
    # def check_or_create_user_id(self, cookies):
    #     user_id = cookies.get("user_id")
    #     if not user_id:
    #         user_id = str(uuid.uuid4())
    #         rx.set_cookie("user_id", user_id, max_age=60*60*24*365)  # 1 year expiry
    #     self.user_id = user_id

    @rx.var
    def is_input_empty(self) -> bool:
        return self.input_text.strip() == ""

    @rx.var
    def is_valid_url(self) -> bool:
        return bool(
            re.match(
                r"^(https?://)?(www\.)?[\w\-]+\.[a-z]{2,}(/[\w\-./?%&=]*)?$",
                self.input_text.strip()
            )
        )

    @rx.event
    async def process_input(self):
        self.is_loading = True  # Show the loader immediately

        url = self.input_text.strip()
        save_user_url(self.user_id, url)

        if not self.is_valid_url:
            self.is_loading = False
            yield rx.toast(
                "Please enter a valid URL.",
                duration=3000,
                close_button=True,
            )
            return

        yield  # Let UI update with loader

        reachable = await check_url_reachable(url)
        if not reachable:
            self.is_loading = False
            yield rx.toast(
                "Website not reachable.",
                description="Ensure it starts with https:// and is reachable.",
                duration=3000,
                close_button=True,
            )
            return

        await main(url)  # Your LLM processing
        yield rx.redirect("/results")  # Loader will disappear on route change automatically

        
      

# ──────────────────────────────────────────────────────────────
# ✅ App Theme
# ──────────────────────────────────────────────────────────────
theme = rx.theme(
    appearance="light",
    accent_color="orange",
    radius="large",
    font="system",
)

# ──────────────────────────────────────────────────────────────
# ✅ Optional: Global loader component
# ──────────────────────────────────────────────────────────────



def index():
    
    return rx.fragment(
        # ⏳ Global loader visible on State.is_loading
        rx.cond(
            State.is_loading,
            rx.center(
                rx.html(
                    """
                    <iframe src="https://lottie.host/embed/c5ea05d5-a299-450c-af25-0ae9c7fc2fba/4DgOchkQ49.lottie"
                            style="width: 380px; height: 380px; border: none; background: none;" 
                            allowfullscreen>
                    </iframe>
                    """
                ),
                style={
                    "position": "fixed",
                    "top": "0",
                    "left": "0",
                    "width": "100vw",
                    "height": "100vh",
                    "backgroundColor": "rgba(255,255,255,0.6)",
                    "backdropFilter": "blur(6px)",
                    "zIndex": "9999",
                    "pointerEvents": "none",
                    "opacity": rx.cond(State.is_loading, "1", "0"),  # ✅ Fix applied her
                    "transition": "opacity 0.5s ease-in-out",
                }
            )
        ),

    rx.center(    
        rx.vstack(
            # --------- Section One (Hero with tagline) ---------
            rx.vstack(

            # Noise overlay
            rx.box(
                style={
                    "position": "absolute",
                    "top": "0",
                    "left": "0",
                    "width": "100%",
                    "height": "100%",
                    "backgroundImage": "url('https://grainy-gradients.vercel.app/noise.svg')",
                    "opacity": "0.5",  # very light noise
                    "zIndex": "-2",
                    "pointerEvents": "none",
                }
            ),


                # Tagline badge
                rx.box(
                    rx.text("💥 Turn any website into usable LLM context", size="2"),
                    style={
                        "padding": "0.3rem 1rem",
                        "borderRadius": "9999px",
                        "backgroundColor": "#ffffff",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.05)",
                        "color": "#111111",
                        "fontWeight": "500"
                    }
                ),

                # Hero heading
                rx.vstack(
                    rx.text("Web scraping", size="9", weight="bold", color="#1e1e1d", text_align="center"),
                    rx.text("for AI & agents", size="8", weight="bold", color="#e78642", text_align="center"),
                    spacing="1",
                    align="center",
                     style={
                        "paddingTop": "2.2rem"
                    }
                ),

                # Subheading
                rx.text(
                    "It's also open source.",
                    size="3",
                    color="gray",
                    align="center",
                    style={"maxWidth": "600px"}
                ),

                spacing="4",
                align="center",
            ),

            rx.spacer(),

            # --------- Section Two (Input Box Centered) ---------
            rx.center(
                rx.box(
                    rx.fragment(
                        rx.input(
                            placeholder="Paste Your Website Link ...",
                            value=State.input_text,
                            on_change=State.set_input_text,
                            on_blur=lambda: State.set_show_alert(False),
                            style={
                                "width": "100%",
                                "maxWidth": "820px",
                                "padding": "1rem 3.5rem 1rem 2.5rem",
                                "height": "9.9rem",
                                "borderRadius": "2rem",
                                "boxShadow": "0 4px 10px rgba(0, 0, 0, 0.1)",
                                "border": "1px solid #ccc",
                                "fontSize": "1rem",
                                "position": "relative",
                                "backgroundColor": "transparent",
                            },
                        ),
                        rx.box(
                            rx.image(src="/ai.svg"),
                            style={
                                "position": "absolute",
                                "left": "1rem",
                                "top": "32%",
                                "transform": "translateY(-50%)",
                                "max-width": "29px",
                                "opacity": "0.89",
                            }
                        ),
                        rx.tooltip(
                            rx.button(
                                rx.icon(tag="arrow-up"),
                                size="1",
                                radius="full",
                                color_scheme="orange",
                                disabled = State.is_input_empty | (~State.is_valid_url),
                                on_click=State.process_input,
                                style={
                                    "position": "absolute",
                                    "right": "0.7rem",
                                    "top": "79%",
                                    "transform": "translateY(-50%)",
                                    "minWidth": "4.3rem",
                                    "height": "2.5rem",
                                    "padding": "0",
                                },
                            ),
                            content="Enter Valid Link.",
                        ),
                        rx.center(
                            rx.hstack(
                                rx.switch(
                                    on_change=SwitchState.set_end,
                                    default_checked=SwitchState.value,  # Just visual, not reactive
                                ),
                                rx.badge(SwitchState.mode_text),
                            ),
                            style={
                                "position": "absolute",
                                "left": "1rem",
                                "top": "75%",
                            },
                        ),


                    ),
                    
                    rx.cond(
                        SwitchState.show_modal,
                        rx.center(
                            rx.box(
                                rx.vstack(
                                    rx.hstack(
                                        rx.icon(tag="lock", color="#000000", size=22),  # gold star icon
                                        rx.text("Premium Feature", size="5", weight="bold", color="#000000"),
                                        spacing="2",  # spacing between icon and text
                                        align="center",
                                        justify="center",
                                    ),

                                    rx.text(
                                        "This is a premium feature. Contact admin to unlock.",
                                        size="1",
                                        color="black",
                                        text_align="center",
                                    ),
                                    rx.hstack(
                                        rx.button(
                                            "Contact Admin",
                                            on_click=rx.redirect("mailto:buildbyfiroz@icloud.com"),
                                            size="3",
                                            style={
                                                "backgroundColor": "#F98147",
                                                "color": "#fff",
                                                "fontWeight": "600",
                                                "borderRadius": "1rem",
                                                "padding": "1rem 1.5rem",
                                                "transition": "all 0.3s ease-in-out",
                                            },
                                            _hover={
                                                "backgroundColor": "#e46e35"
                                            }
                                        ),
                                        rx.button(
                                            "Cancel",
                                            on_click=SwitchState.close_modal,
                                            size="3",
                                            style={
                                                "width": "50%",
                                                "backgroundColor": "rgb(220 213 213 / 85%)",
                                                "color": "#333",
                                                "fontWeight": "600",
                                                "borderRadius": "1rem",
                                                "padding": "1rem 1.5rem",
                                                "transition": "all 0.3s ease-in-out",
                                            },
                                            _hover={
                                                "backgroundColor": "#f5f5f5"
                                            }
                                        ),
                                        spacing="3",  # ✅ FIXED: use a valid Reflex spacing value between "0"–"9"
                                        width="100%",
                                    ),
                                    spacing="4",
                                    align="center"
                                ),
                                
                                
                                style={
                                    "width": "400px",
                                    "maxWidth": "90%",
                                    "padding": "2.5rem",
                                    "background": "rgba(239, 230, 222, 0.46)",  # ✅ fixed missing closing )
                                    "borderRadius": "16px",                     # ✅ camelCase and removed ;
                                    "backdropFilter": "blur(3px)",              # ✅ removed ; and camelCase
                                    "WebkitBackdropFilter": "blur(3px)",        # ✅ removed ; and camelCase
                                    "position": "relative",
                                    "overflow": "hidden",
                                    "zIndex": "9999",
                                }


                            ),
                            style={
                                "position": "fixed",
                                "top": "0",
                                "left": "0",
                                "width": "100vw",
                                "height": "100vh",
                                "background": "rgba(0, 0, 0, 0.4)",
                                "zIndex": "9998"
                            }
                        )
                    ),

                    
                    
                    style={
                        "position": "relative",
                        "width": "100%",
                        "maxWidth": "820px",
                    }
                )
            ),

            rx.spacer(),

            # --------- Section Three (Logos) ---------
            rx.vstack(
                rx.text("Adopted by 10K+ companies", size="2", color="gray", style={"fontWeight": "500"}),
                rx.hstack(
                    # Cloudflare (left-faded)
                    rx.box(
                        rx.image(src="https://www.firecrawl.dev/logos/openai.png", style={
                            "objectFit": "contain",
                            "width": "100%",
                            "height": "100%",
                        }),
                        style={
                            "width": "clamp(60px, 10vw, 100px)",   # responsive
                            "height": "clamp(24px, 4vw, 40px)",   # responsive
                            "WebkitMaskImage": "linear-gradient(to right, rgba(0,0,0,0.2), rgba(0,0,0,1))",
                            "maskImage": "linear-gradient(to right, rgba(0,0,0,0.2), rgba(0,0,0,1))",
                            "filter": "grayscale(100%)"
                        },
                    ),

                    # Stripe
                    rx.box(
                        rx.image(src="/stripe.svg", style={
                            "objectFit": "contain",
                            "width": "100%",
                            "height": "100%",
                        }),
                        class_name="hide-on-small",
                        style={
                            "width": "clamp(60px, 10vw, 100px)",
                            "height": "clamp(24px, 4vw, 40px)",
                            "filter": "grayscale(100%)"
                        },
                    ),

                    # Zapier
                    rx.box(
                        rx.image(src="/zapier.svg", style={
                            "objectFit": "contain",
                            "width": "100%",
                            "height": "100%",
                        }),
                        style={
                            "width": "clamp(60px, 10vw, 100px)",
                            "height": "clamp(24px, 4vw, 40px)",
                            "filter": "grayscale(100%)"
                        },
                    ),

                    # NVIDIA
                    rx.box(
                        rx.image(src="https://www.firecrawl.dev/logos/nvidia-com.png", style={
                            "objectFit": "contain",
                            "width": "100%",
                            "height": "100%",
                        }),
                        style={
                            "width": "clamp(60px, 10vw, 100px)",
                            "height": "clamp(24px, 4vw, 40px)",
                            "filter": "grayscale(100%)"
                        },
                    ),

                    # Gamma (right-faded)
                    rx.box(
                        rx.image(src="https://www.firecrawl.dev/logos/gamma.svg", style={
                            "objectFit": "contain",
                            "width": "100%",
                            "height": "100%",
                        }),
                        style={
                            "width": "clamp(60px, 10vw, 100px)",
                            "height": "clamp(24px, 4vw, 40px)",
                            "WebkitMaskImage": "linear-gradient(to left, rgba(0,0,0,0.2), rgba(0,0,0,1))",
                            "maskImage": "linear-gradient(to left, rgba(0,0,0,0.2), rgba(0,0,0,1))",
                            "filter": "grayscale(100%)"
                        },
                    ),

        spacing="5",
        justify="center",
        wrap="wrap",  # makes it wrap on smaller screens
        
        
        
        
    
    
    ),
    spacing="3",
    align="center",
            ),
            
            
            
            

            spacing="6",
            justify="center",
            align="center",
            style={
                "paddingTop": "3rem",
                "paddingBottom": "3rem",
                "width": "100%",
                "height": "100%",
            }
            
            
        
        ),
        
      
        
        
        style={
            "background": "linear-gradient(to right, #ffffff, #e4b38d5c)",
            "height": "100vh",
            "overflow": "hidden",
            "padding": "0",
            "backdropFilter": "blur(4px)",
            "WebkitBackdropFilter": "blur(4px)",

        }
    ),
    ),




#app = rx.App(theme=theme, stylesheets="/styles.css",)
app = rx.App(
    theme=theme,
    stylesheets=[
        "/styles.css",  # This path is relative to assets/
    ],
)

# Register pages
app.add_page(index)
#app.add_page(result_page, route='/results')

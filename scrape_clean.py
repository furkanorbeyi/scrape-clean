#!/usr/bin/env python3


import time
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import threading
import sys
import os
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ScrapeCleanPro:
    def __init__(self, root):
        self.root = root
        self.root.title("ScrapeClean")
        self.root.geometry("650x450")
        self.configure_styles()
        self.create_widgets()
        self.driver = None
        
    def configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", font=("Segoe UI", 10), foreground="#333")
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), borderwidth=1)
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Hedef URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_url = ttk.Entry(main_frame, width=70)
        self.entry_url.grid(row=0, column=1, pady=5, padx=10)

        ttk.Label(main_frame, text="CSS Seçici:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_selector = ttk.Entry(main_frame, width=70)
        self.entry_selector.grid(row=1, column=1, pady=5, padx=10)

        ttk.Label(main_frame, text="Çıktı Dosyası:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.entry_output = ttk.Entry(main_frame, width=70)
        self.entry_output.insert(0, "veriler.csv")
        self.entry_output.grid(row=2, column=1, pady=5, padx=10)

        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, 
                                      length=450, mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=2, pady=20)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2)

        self.btn_start = ttk.Button(btn_frame, text="Başlat", command=self.start_scraping_thread)
        self.btn_start.pack(side=tk.LEFT, padx=10)

        self.btn_exit = ttk.Button(btn_frame, text="Çıkış", command=self.safe_exit)
        self.btn_exit.pack(side=tk.LEFT)

    def start_scraping_thread(self):
        if self.driver and hasattr(self.driver, 'service') and self.driver.service.process:
            try:
                self.driver.quit()
            except:
                pass
        threading.Thread(target=self.run_scraping, daemon=True).start()

    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update_idletasks()

    def init_driver(self):
        try:
            chrome_options = webdriver.ChromeOptions()
            
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-gpu')

            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')

            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            os.environ['WDM_LOCAL_PATH'] = os.path.expanduser('~')
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            })

            self.driver.set_page_load_timeout(30)
            return True
            
        except Exception as e:
            messagebox.showerror("Driver Hatası", f"Driver başlatılamadı: {str(e)}")
            return False

    def wait_for_element(self, selector, timeout=20):
        """Belirli bir CSS seçiciye sahip elementin yüklenmesini bekle"""
        try:
            self.driver.execute_script("return document.readyState") == "complete"

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)

            self.driver.execute_script("""
                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });
            """)
            time.sleep(1)

            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return True
            except:
                try:
                    element = self.driver.execute_script(f"""
                        return document.querySelector("{selector}");
                    """)
                    return element is not None
                except:
                    return False
                    
        except Exception as e:
            print(f"Bekleme hatası: {str(e)}")
            return False

    def fetch_html(self, url, selector):
        try:
            self.driver.get(url)
            time.sleep(3)  
        
            self.driver.refresh()
            time.sleep(2)
            
            if not self.wait_for_element(selector):
                alternative_selectors = [
                    selector,
                    f'[class*="{selector.replace(".", "")}"]',
                    f'div{selector}', selector.replace(".", ""),
                ]
                
                for alt_selector in alternative_selectors:
                    if self.wait_for_element(alt_selector):
                        return self.driver.page_source
                        
                messagebox.showwarning("Uyarı", "Seçilen element bulunamadı. Lütfen seçiciyi kontrol edin.")
                return None
                
            return self.driver.page_source
            
        except Exception as e:
            messagebox.showerror("Yükleme Hatası", f"Sayfa yüklenemedi: {str(e)}")
            return None

    def parse_data(self, html, selector):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            elements = soup.select(selector)
            
            if not elements:
                elements = soup.select(selector.replace('.', ''))
            
            data = [elem.get_text(strip=True) for elem in elements if elem.text.strip()]
            
            if not data:
                try:
                    data = [elem.text.strip() for elem in self.driver.find_elements(By.CSS_SELECTOR, selector)]
                except:
                    pass
                
            return data
        except Exception as e:
            messagebox.showerror("Parse Hatası", f"Veri ayrıştırma başarısız: {str(e)}")
            return []

    def run_scraping(self):
        try:
            self.btn_start['state'] = tk.DISABLED
            self.update_progress(0)
            
            url = self.entry_url.get().strip()
            selector = self.entry_selector.get().strip()
            output = self.entry_output.get().strip() or "veriler.csv"

            if not url.startswith(('http://', 'https://')):
                raise ValueError("Geçersiz URL formatı")
                
            if not self.init_driver():
                return

            self.update_progress(25)
            html = self.fetch_html(url, selector)
            
            self.update_progress(50)
            if not html:
                return

            data = self.parse_data(html, selector)
            self.update_progress(75)
            
            if not data:
                messagebox.showinfo("Sonuç", "Hedef veri bulunamadı")
                return

            pd.DataFrame(data, columns=["Veri"]).to_csv(output, index=False, encoding='utf-8-sig')
            messagebox.showinfo("Başarılı", f"Veriler kaydedildi:\n{output}")
            
        except Exception as e:
            messagebox.showerror("Kritik Hata", f"{str(e)}")
        finally:
            self.update_progress(100)
            time.sleep(0.5)
            self.progress['value'] = 0
            self.btn_start['state'] = tk.NORMAL
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

    def safe_exit(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScrapeCleanPro(root)
    root.protocol("WM_DELETE_WINDOW", app.safe_exit)
    root.mainloop()
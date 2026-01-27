"""
compact_trader.py - MINIMAL ALWAYS-ON-TOP TRADING UI (FIXED TSL)
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import asyncio
from datetime import datetime, timedelta
import time
import os
import sys

# Import trading modules
from shared import TradeDirection, logger
from flattrade_api_simple import FlattradeAPISimple
from order_manager import OrderManager
from smart_entry import SmartEntryEngine
from spot_analyzer import SpotAnalyzer
from option_pricer import OptionPricer
from get_access_token_fixed import get_access_token

# FIXED: Import the CORRECT TSL Manager
try:
    from tsl_manager_fixed import TSLManagerFixed as TSLManager
    print("✅ Using CORRECT TSL Manager (Phase-wise)")
except ImportError:
    # Fallback to old one if new not available
    try:
        from tsl_manager import TSLManager
        print("⚠️ Using OLD TSL Manager (update to tsl_manager_fixed.py)")
    except ImportError:
        print("❌ No TSL Manager found")
        # Create dummy class
        class TSLManager:
            async def start_management(self, position):
                print("⚠️ DUMMY TSL Manager - No actual management")
                return True
            async def exit_position(self, reason):
                print(f"⚠️ DUMMY Exit: {reason}")
            async def emergency_exit(self):
                print("⚠️ DUMMY Emergency Exit")

class CompactTrader:
    """Compact Always-On-Top Trading UI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀")
        self.root.geometry("400x600")
        
        # ALWAYS ON TOP
        self.root.attributes('-topmost', True)
        
        # Minimize to system tray option
        self.minimized = False
        
        # Initialize components
        self.initialize_system()
        
        # Setup compact UI
        self.setup_ui()
        
        # Auto token refresh
        self.setup_token_refresh()
        
        # Start updates
        self.update_interval = 3000  # 3 seconds
        self.update_dashboard()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
    def initialize_system(self):
        """Initialize trading system"""
        print("🔧 Initializing Trading System...")
        
        # Check and refresh token
        self.refresh_access_token()
        
        # Initialize API
        self.api = FlattradeAPISimple()
        
        # Initialize managers
        self.order_manager = OrderManager(self.api)
        self.spot_analyzer = SpotAnalyzer(self.api)
        self.option_pricer = OptionPricer(self.api)
        self.smart_entry = SmartEntryEngine(
            order_executor=self.order_manager,
            spot_analyzer=self.spot_analyzer,
            option_pricer=self.option_pricer
        )
        
        # FIXED: Initialize CORRECT TSL Manager
        self.tsl_manager = TSLManager(self.order_manager, self.api)
        self.current_position = None
        
        print("✅ System initialized with PHASE-WISE TSL")
    
    def refresh_access_token(self):
        """Refresh access token if needed"""
        try:
            from credentials import ACCESS_TOKEN
            
            if not ACCESS_TOKEN or ACCESS_TOKEN == "" or len(ACCESS_TOKEN) < 50:
                print("🔑 Token missing or expired, refreshing...")
                token = get_access_token()
                if token:
                    print("✅ Token refreshed successfully")
                    return True
                else:
                    print("❌ Token refresh failed")
                    return False
            return True
            
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
            return False
    
    def setup_token_refresh(self):
        """Schedule automatic token refresh"""
        # Check token every 30 minutes
        self.root.after(30 * 60 * 1000, self.auto_refresh_token)
    
    def auto_refresh_token(self):
        """Auto refresh token"""
        if self.refresh_access_token():
            self.log("✅ Token auto-refreshed")
        
        # Schedule next refresh
        self.root.after(30 * 60 * 1000, self.auto_refresh_token)
    
    def setup_ui(self):
        """Setup compact UI"""
        
        # ================= HEADER =================
        header_frame = tk.Frame(self.root, bg="black", height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="🚀 MICRO SCALPER", 
            fg="white", 
            bg="black",
            font=("Arial", 12, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Time
        self.time_label = tk.Label(
            header_frame,
            fg="yellow",
            bg="black",
            font=("Arial", 10)
        )
        self.time_label.pack(side=tk.RIGHT, padx=10)
        
        # ================= MARKET STATUS =================
        status_frame = tk.Frame(self.root, bg="#f0f0f0", height=30)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="⏳ Checking...",
            bg="#f0f0f0",
            font=("Arial", 9, "bold")
        )
        self.status_label.pack(pady=5)
        
        # ================= SPOT PRICE =================
        spot_frame = tk.Frame(self.root, bg="white", height=50)
        spot_frame.pack(fill=tk.X, pady=5)
        spot_frame.pack_propagate(False)
        
        tk.Label(
            spot_frame, 
            text="NIFTY:", 
            bg="white",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=10)
        
        self.spot_label = tk.Label(
            spot_frame,
            text="₹0.00",
            bg="white",
            font=("Arial", 16, "bold")
        )
        self.spot_label.pack(side=tk.LEFT)
        
        # P&L
        self.pnl_label = tk.Label(
            spot_frame,
            text="P&L: ₹0.00",
            bg="white",
            font=("Arial", 10)
        )
        self.pnl_label.pack(side=tk.RIGHT, padx=10)
        
        # ================= TRADING BUTTONS =================
        button_frame = tk.Frame(self.root, bg="white")
        button_frame.pack(fill=tk.X, pady=10)
        
        # CE Button (GREEN)
        self.buy_ce_btn = tk.Button(
            button_frame,
            text="🟢 BUY CE",
            command=self.buy_ce,
            bg="#90EE90",  # Light green
            fg="black",
            font=("Arial", 12, "bold"),
            height=2,
            width=15,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.buy_ce_btn.pack(pady=5)
        
        # PE Button (RED)
        self.buy_pe_btn = tk.Button(
            button_frame,
            text="🔴 BUY PE",
            command=self.buy_pe,
            bg="#FFB6C1",  # Light red
            fg="black",
            font=("Arial", 12, "bold"),
            height=2,
            width=15,
            relief=tk.RAISED,
            borderwidth=3
        )
        self.buy_pe_btn.pack(pady=5)
        
        # Exit Button (YELLOW)
        self.exit_btn = tk.Button(
            button_frame,
            text="🟡 EXIT",
            command=self.exit_position,
            bg="#FFFACD",  # Light yellow
            fg="black",
            font=("Arial", 11, "bold"),
            height=2,
            width=12,
            state=tk.DISABLED
        )
        self.exit_btn.pack(pady=5)
        
        # ================= POSITION INFO =================
        pos_frame = tk.LabelFrame(self.root, text="POSITION", font=("Arial", 9, "bold"))
        pos_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Grid for position details
        pos_grid = tk.Frame(pos_frame)
        pos_grid.pack(padx=5, pady=5)
        
        # Labels
        labels = [
            ("Symbol:", "symbol_val"),
            ("Entry:", "entry_val"),
            ("LTP:", "ltp_val"),
            ("SL:", "sl_val"),
            ("TSL:", "tsl_val"),
            ("MTM:", "mtm_val"),
            ("Phase:", "phase_val")  # ADDED: Show current phase
        ]
        
        for i, (label, var) in enumerate(labels):
            # Label
            tk.Label(
                pos_grid,
                text=label,
                font=("Arial", 8)
            ).grid(row=i, column=0, sticky="e", padx=2, pady=2)
            
            # Value
            value_label = tk.Label(
                pos_grid,
                text="---",
                font=("Arial", 8, "bold")
            )
            value_label.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            setattr(self, var, value_label)
        
        # ================= QUICK ACTIONS =================
        action_frame = tk.Frame(self.root)
        action_frame.pack(fill=tk.X, pady=10)
        
        # Emergency Exit
        self.emergency_btn = tk.Button(
            action_frame,
            text="🚨 EMERGENCY",
            command=self.emergency_exit,
            bg="red",
            fg="white",
            font=("Arial", 9, "bold"),
            height=1,
            width=12,
            state=tk.DISABLED
        )
        self.emergency_btn.pack(side=tk.LEFT, padx=5)
        
        # Hide/Show
        self.hide_btn = tk.Button(
            action_frame,
            text="⬇️ MINIMIZE",
            command=self.minimize_ui,
            bg="gray",
            fg="white",
            font=("Arial", 9),
            height=1,
            width=12
        )
        self.hide_btn.pack(side=tk.RIGHT, padx=5)
        
        # ================= LOGS =================
        log_frame = tk.LabelFrame(self.root, text="LOGS", font=("Arial", 9, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(
            log_frame,
            height=8,
            width=40,
            font=("Courier", 8),
            wrap=tk.WORD,
            bg="black",
            fg="white"
        )
        
        log_scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initial log
        self.log("✅ System started with PHASE-WISE TSL")
        self.log(f"📅 {datetime.now().strftime('%H:%M:%S')}")
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        # Limit log size
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 50:
            self.log_text.delete("1.0", f"{len(lines)-40}.0")
        
        self.log_text.see(tk.END)
    
    def update_dashboard(self):
        """Update all UI elements"""
        try:
            # Update time
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.config(text=current_time)
            
            # Update market data
            self.update_market_data()
            
            # Update position if exists
            if self.current_position and self.tsl_manager:
                self.update_position_display()
            
            # Check market hours
            self.check_market_hours()
            
            # Update button states
            self.update_button_states()
            
        except Exception as e:
            self.log(f"❌ Update error: {e}")
        
        # Schedule next update
        self.root.after(self.update_interval, self.update_dashboard)
    
    def update_market_data(self):
        """Update market data"""
        try:
            # Mock spot for now - replace with real API
            import random
            nifty_spot = 19500.50 + random.uniform(-50, 50)
            self.spot_label.config(text=f"₹{nifty_spot:.2f}")
            
        except Exception as e:
            pass
    
    def update_position_display(self):
        """Update position information"""
        if not self.current_position:
            return
        
        try:
            # Get current price
            current_price = self.api.get_ltp(self.current_position.symbol)
            
            # Calculate MTM
            mtm = (current_price - self.current_position.entry_price) * self.current_position.qty
            
            # Update labels
            self.symbol_val.config(text=self.current_position.symbol[-15:])
            self.entry_val.config(text=f"₹{self.current_position.entry_price:.2f}")
            self.ltp_val.config(text=f"₹{current_price:.2f}")
            self.sl_val.config(text=f"₹{self.current_position.tsl:.2f}")
            self.tsl_val.config(text=f"₹{self.current_position.tsl:.2f}")
            
            # Show phase if available
            if hasattr(self.current_position, 'phase'):
                self.phase_val.config(text=self.current_position.phase)
            else:
                self.phase_val.config(text="MICRO")
            
            # MTM with color
            mtm_color = "green" if mtm >= 0 else "red"
            self.mtm_val.config(text=f"₹{mtm:.2f}", fg=mtm_color)
            self.pnl_label.config(text=f"P&L: ₹{mtm:.2f}")
            
        except Exception as e:
            self.log(f"❌ Position update error: {e}")
    
    def check_market_hours(self):
        """Check if market is open"""
        now = datetime.now()
        current_time = now.time()
        
        # Market hours: 9:15 to 15:30, Monday-Friday
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        is_market_open = (market_open <= current_time <= market_close) and (now.weekday() < 5)
        
        if is_market_open:
            self.status_label.config(
                text="✅ MARKET OPEN", 
                bg="#d4edda", 
                fg="#155724"
            )
        else:
            self.status_label.config(
                text="⏳ MARKET CLOSED", 
                bg="#f8d7da", 
                fg="#721c24"
            )
    
    def update_button_states(self):
        """Update button states based on market and position"""
        now = datetime.now()
        current_time = now.time()
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        is_market_open = (market_open <= current_time <= market_close) and (now.weekday() < 5)
        
        if is_market_open and not self.current_position:
            self.buy_ce_btn.config(state=tk.NORMAL)
            self.buy_pe_btn.config(state=tk.NORMAL)
            self.exit_btn.config(state=tk.DISABLED)
            self.emergency_btn.config(state=tk.DISABLED)
        elif self.current_position:
            self.buy_ce_btn.config(state=tk.DISABLED)
            self.buy_pe_btn.config(state=tk.DISABLED)
            self.exit_btn.config(state=tk.NORMAL)
            self.emergency_btn.config(state=tk.NORMAL)
        else:
            self.buy_ce_btn.config(state=tk.DISABLED)
            self.buy_pe_btn.config(state=tk.DISABLED)
            self.exit_btn.config(state=tk.DISABLED)
            self.emergency_btn.config(state=tk.DISABLED)
    
    # ================= TRADING FUNCTIONS =================
    
    def buy_ce(self):
        """Execute CE buy"""
        self.log("🚀 BUY CE triggered...")
        self.log("Phase 1: +1/+2/+3/+4/+5 trailing will activate")
        self.buy_ce_btn.config(state=tk.DISABLED)
        
        threading.Thread(target=self._execute_buy_ce, daemon=True).start()
    
    def _execute_buy_ce(self):
        """Execute CE buy in background"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            entry_result = loop.run_until_complete(
                self.smart_entry.execute_entry(TradeDirection.CE)
            )
            
            if entry_result:
                symbol, avg_price, entry_orders = entry_result
                
                # Create position with phase info
                from models import Position
                self.current_position = Position(
                    symbol=symbol,
                    qty=sum(order.quantity for order in entry_orders),
                    entry_price=avg_price,
                    direction=TradeDirection.CE
                )
                
                # FIXED: Start CORRECT TSL management
                loop.run_until_complete(
                    self.tsl_manager.start_management(self.current_position)
                )
                
                self.log(f"✅ CE BUY: {symbol}")
                self.log(f"   Entry: ₹{avg_price:.2f}")
                self.log(f"   Phase 1: +1/+2/+3/+4/+5 trailing ACTIVE")
                
                # Show phase in UI
                if hasattr(self.current_position, 'phase'):
                    self.log(f"   Current Phase: {self.current_position.phase}")
                
            else:
                self.log("❌ CE buy failed")
                
        except Exception as e:
            self.log(f"❌ CE buy error: {e}")
        
        finally:
            self.root.after(1000, self.update_button_states)
    
    def buy_pe(self):
        """Execute PE buy"""
        self.log("🚀 BUY PE triggered...")
        self.log("Phase 1: +1/+2/+3/+4/+5 trailing will activate")
        self.buy_pe_btn.config(state=tk.DISABLED)
        
        threading.Thread(target=self._execute_buy_pe, daemon=True).start()
    
    def _execute_buy_pe(self):
        """Execute PE buy in background"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            entry_result = loop.run_until_complete(
                self.smart_entry.execute_entry(TradeDirection.PE)
            )
            
            if entry_result:
                symbol, avg_price, entry_orders = entry_result
                
                from models import Position
                self.current_position = Position(
                    symbol=symbol,
                    qty=sum(order.quantity for order in entry_orders),
                    entry_price=avg_price,
                    direction=TradeDirection.PE
                )
                
                # FIXED: Start CORRECT TSL management
                loop.run_until_complete(
                    self.tsl_manager.start_management(self.current_position)
                )
                
                self.log(f"✅ PE BUY: {symbol}")
                self.log(f"   Entry: ₹{avg_price:.2f}")
                self.log(f"   Phase 1: +1/+2/+3/+4/+5 trailing ACTIVE")
                
                # Show phase in UI
                if hasattr(self.current_position, 'phase'):
                    self.log(f"   Current Phase: {self.current_position.phase}")
                
            else:
                self.log("❌ PE buy failed")
                
        except Exception as e:
            self.log(f"❌ PE buy error: {e}")
        
        finally:
            self.root.after(1000, self.update_button_states)
    
    def exit_position(self):
        """Exit current position"""
        if not self.current_position or not self.tsl_manager:
            self.log("⚠️ No active position")
            return
        
        self.log("🔄 Manual exit...")
        
        threading.Thread(target=self._execute_exit, daemon=True).start()
    
    def _execute_exit(self):
        """Execute exit in background"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Exit position using CORRECT TSL manager
            loop.run_until_complete(
                self.tsl_manager.exit_position("MANUAL_EXIT")
            )
            
            # Calculate final P&L
            if self.current_position:
                current_price = self.api.get_ltp(self.current_position.symbol)
                mtm = (current_price - self.current_position.entry_price) * self.current_position.qty
                self.log(f"✅ Exit complete. P&L: ₹{mtm:.2f}")
            
            # Clear position
            self.current_position = None
            
            # Reset UI
            self.root.after(0, self.reset_position_display)
            
        except Exception as e:
            self.log(f"❌ Exit error: {e}")
        
        finally:
            self.root.after(1000, self.update_button_states)
    
    def emergency_exit(self):
        """Emergency exit"""
        if not self.current_position:
            return
        
        if messagebox.askyesno("🚨 EMERGENCY EXIT", 
                               "Exit IMMEDIATELY at market price?"):
            self.log("🚨 EMERGENCY EXIT!")
            
            threading.Thread(target=self._execute_emergency_exit, daemon=True).start()
    
    def _execute_emergency_exit(self):
        """Emergency exit at market price"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Place market order directly
            exit_result = loop.run_until_complete(
                self.order_manager.place_market_order(
                    symbol=self.current_position.symbol,
                    side="SELL" if self.current_position.direction == TradeDirection.CE else "BUY",
                    qty=self.current_position.qty,
                    tag="EMERGENCY_EXIT"
                )
            )
            
            if exit_result.get("success"):
                self.log("✅ Emergency exit executed")
                
                # Stop TSL manager
                if self.tsl_manager:
                    loop.run_until_complete(self.tsl_manager.emergency_exit())
                
                # Clear position
                self.current_position = None
                
                # Reset UI
                self.root.after(0, self.reset_position_display)
                
            else:
                self.log("❌ Emergency exit failed")
                
        except Exception as e:
            self.log(f"❌ Emergency exit error: {e}")
        
        finally:
            self.root.after(1000, self.update_button_states)
    
    def reset_position_display(self):
        """Reset position display"""
        labels = [self.symbol_val, self.entry_val, self.ltp_val, 
                 self.sl_val, self.tsl_val, self.mtm_val, self.phase_val]
        
        for label in labels:
            label.config(text="---", fg="black")
        
        self.pnl_label.config(text="P&L: ₹0.00")
    
    def minimize_ui(self):
        """Minimize UI to compact mode"""
        if not self.minimized:
            # Save current size
            self.saved_geometry = self.root.geometry()
            
            # Minimize to title bar only
            self.root.geometry("400x120")
            
            # Hide all except header
            for widget in self.root.winfo_children():
                if widget != self.root.winfo_children()[0]:  # Not header
                    widget.pack_forget()
            
            self.hide_btn.config(text="⬆️ RESTORE")
            self.minimized = True
            self.log("⬇️ UI minimized")
        else:
            # Restore
            self.root.geometry(self.saved_geometry)
            
            # Re-add widgets
            self.setup_ui_after_minimize()
            
            self.hide_btn.config(text="⬇️ MINIMIZE")
            self.minimized = False
            self.log("⬆️ UI restored")
    
    def setup_ui_after_minimize(self):
        """Re-setup UI after minimize"""
        # Remove all widgets except header
        for widget in self.root.winfo_children()[1:]:
            widget.destroy()
        
        # Re-create UI (excluding header which is already there)
        self.setup_ui()
    
    def minimize_to_tray(self):
        """Minimize to system tray (actually just hide)"""
        self.root.withdraw()  # Hide window
        
        # Create system tray icon (simplified)
        self.create_tray_icon()
    
    def create_tray_icon(self):
        """Create system tray icon (simplified for now)"""
        # For now, just show message
        self.log("📌 Minimized to background")
        print("App running in background. Check logs for updates.")
        
        # You can add actual system tray icon here
        # Using pystray or similar library
    
    def restore_from_tray(self):
        """Restore from system tray"""
        self.root.deiconify()  # Show window
        self.log("📌 Restored from background")

def main():
    """Main function"""
    print("\n" + "="*60)
    print("🚀 MICRO SCALPER - PHASE-WISE TSL TRADING")
    print("="*60)
    print("Phase 1: +1/+2/+3/+4/+5 micro trailing")
    print("Phase 2: Spike detection & immediate exit")
    print("Phase 3: ATR based trailing")
    print("="*60)
    
    app = CompactTrader()
    app.root.mainloop()

if __name__ == "__main__":
    main()
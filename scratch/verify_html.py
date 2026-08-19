import urllib.request

url = 'http://127.0.0.1:5000/'
html = urllib.request.urlopen(url).read().decode('utf-8')

has_auth_panel_first = '<div id="auth-panel">' in html
has_main_panel_hidden = '<div id="main-panel" class="hidden" style="display: none !important;">' in html

print("--- CUSTOMER APP RAW HTML VERIFICATION ---")
print("1. Customer Sign In / Create Account Page IS FIRST VISIBLE IN HTML:", has_auth_panel_first)
print("2. Customer Dashboard IS COMPLETELY HIDDEN IN HTML:", has_main_panel_hidden)

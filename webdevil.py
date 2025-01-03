import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

BANNER = r"""
                                                                                                              
                                           _______                                             .---.          
                   __.....__     /|        \  ___ `'.         __.....__   .----.     .----..--.|   |          
       _     _ .-''         '.   ||         ' |--.\  \    .-''         '.  \    \   /    / |__||   |          
 /\    \\   ///     .-''"'-.  `. ||         | |    \  '  /     .-''"'-.  `. '   '. /'   /  .--.|   |          
 `\\  //\\ ///     /________\   \||  __     | |     |  '/     /________\   \|    |'    /   |  ||   |          
   \`//  \'/ |                  |||/'__ '.  | |     |  ||                  ||    ||    |   |  ||   |          
    \|   |/  \    .-------------'|:/`  '. ' | |     ' .'\    .-------------''.   `'   .'   |  ||   |          
     '        \    '-.____...---.||     | | | |___.' /'  \    '-.____...---. \        /    |  ||   |          
               `.             .' ||\    / '/_______.'/    `.             .'   \      /     |__||   |          
                 `''-...... -'   |/\'..' / \_______|/       `''-...... -'      '----'          '---'          
                                 '  `'-'`                                                                     
"""

def main():
    print(BANNER)
    print("Welcome to WebDevil: Advanced Web Scanner by BlackHack\n")

    # Get user input
    url = input("Enter the website URL (e.g., https://example.com): ").strip()
    keyword = input("Enter the word to search for: ").strip()

    # Ensure proper URL format
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Initialize results
        console_results = []
        network_results = []
        dom_matches = []
        js_files = []
        metadata_matches = []
        subpages = set()

        def on_console_message(msg):
            if keyword in msg.text:
                console_results.append(msg.text)

        def on_response(response):
            try:
                body = response.body().decode('utf-8', errors='ignore')
                if keyword in body:
                    lines_with_keyword = [line for line in body.splitlines() if keyword in line]
                    network_results.append(f"URL: {response.url}\nStatus: {response.status}\nMatches:\n" + "\n".join(lines_with_keyword) + "\n")
            except Exception:
                pass

        # Attach listeners
        page.on("console", on_console_message)
        page.on("response", on_response)

        # Visit the URL
        print(f"[+] Navigating to: {url}")
        page.goto(url)

        # Search DOM
        print(f"[+] Searching DOM for keyword: {keyword}")
        dom_matches = page.evaluate(f"""
            () => {{
                const matches = [];
                const elements = document.querySelectorAll("*");
                elements.forEach(el => {{
                    if (el.textContent.includes("{keyword}")) {{
                        matches.push(el.outerHTML);
                    }}
                }});
                return matches;
            }}
        """)

        # Extract internal links (subpages)
        print("[+] Extracting internal links...")
        links = page.evaluate("""
            () => Array.from(document.querySelectorAll('a'))
                .map(link => link.href)
                .filter(href => href.startsWith(window.location.origin))
        """)
        subpages.update(links)

        # Scan each subpage
        print("[+] Scanning subpages for keyword...")
        for subpage in subpages:
            print(f"[+] Scanning subpage: {subpage}")
            try:
                page.goto(subpage)
                body = page.content()
                if keyword in body:
                    dom_matches.append(f"Subpage URL: {subpage}\nMatches:\n" + "\n".join(
                        [line for line in body.splitlines() if keyword in line]))
            except Exception as e:
                print(f"[-] Error scanning subpage {subpage}: {e}")

        # Search for JavaScript files
        print("[+] Searching for JavaScript files...")
        js_files = page.evaluate("""
            () => Array.from(document.querySelectorAll('script')).map(script => script.src).filter(src => src)
        """)

        # Extract metadata
        print("[+] Extracting metadata...")
        metadata_matches = page.evaluate("""
            () => {
                const metas = document.querySelectorAll('meta');
                return Array.from(metas).map(meta => ({
                    name: meta.getAttribute('name'),
                    content: meta.getAttribute('content')
                })).filter(meta => meta.content && meta.content.includes("%s"));
            }
        """ % keyword)

        # Save results to a file
        results_folder = "scan_results"
        os.makedirs(results_folder, exist_ok=True)

        with open(os.path.join(results_folder, "console_logs.txt"), "w") as f:
            f.write("\n".join(console_results))

        with open(os.path.join(results_folder, "network_matches.txt"), "w") as f:
            f.write("\n".join(network_results))

        with open(os.path.join(results_folder, "dom_matches.html"), "w") as f:
            f.write("\n".join(dom_matches))

        with open(os.path.join(results_folder, "javascript_files.txt"), "w") as f:
            f.write("\n".join(js_files))

        with open(os.path.join(results_folder, "metadata_matches.txt"), "w") as f:
            f.write("\n".join([f"Name: {m['name']}, Content: {m['content']}" for m in metadata_matches]))

        with open(os.path.join(results_folder, "subpages.txt"), "w") as f:
            f.write("\n".join(subpages))

        print("[+] Results saved to the 'scan_results' folder.")
        browser.close()

if __name__ == "__main__":
    main()


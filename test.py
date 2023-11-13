from agent.Environment.environments import BrowserEnvironment 

if __name__ == "__main__":
    env = BrowserEnvironment(headless=True,max_page_length=8192,slow_mo=3000,observation_type="accessibility_tree")
    obs,info = env.reset("https://p4psearch.1688.com/hamlet.html?scene=2&keywords=%E6%B7%98%E5%AE%9D&cosite=bingjj&msclkid=6a5cadb74e281a56f267c8e6f111e8d5")
    
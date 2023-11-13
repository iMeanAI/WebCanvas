from agent.Environment.environments import BrowserEnvironment 

if __name__ == "__main__":
    env = BrowserEnvironment(headless=True,max_page_length=8192,slow_mo=3000,observation_type="accessibility_tree")
    obs,info = env.reset("https://aws.amazon.com/cn/campaigns/freecenter/?sc_channel=PS&sc_campaign=acquisition_CN&sc_publisher=baidu&sc_category=pc&sc_medium=%E5%93%81%E7%89%8C_%E6%A0%B8%E5%BF%83%E5%93%81%E7%89%8C%E8%AF%8D_b&sc_content=%E6%A0%B8%E5%BF%83%E5%93%81%E7%89%8C%E8%AF%8D_%E7%B2%BE&sc_detail=aws&sc_segment=JK-AWS%20b1&sc_matchtype=exact&sc_country=CN&trk=c3defc17-b9e8-4474-b125-209d35aff5a5")
    
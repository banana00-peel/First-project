db = [{"name":"杭州西湖","location":"192,38"},
      {"name":"武汉东湖","location":"180,39"},
      {"name":"北京没湖","location":"185,50"},
      {"name":"南京太湖","location":"190,40"}
]

for p in db:
    print(p.get("name"))
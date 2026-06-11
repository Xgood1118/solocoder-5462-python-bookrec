import json
import os
import random
from pathlib import Path
from datetime import datetime, timedelta


BOOK_CATEGORIES = {
    "科幻": {
        "tags": ["科幻", "太空", "未来", "人工智能", "机器人", "时间旅行", "外星人", "赛博朋克", "末世", "星际"],
        "color": "deepblue",
        "authors": ["刘慈欣", "阿西莫夫", "阿瑟·克拉克", "郝景芳", "王晋康", "何夕", "韩松"],
        "publishers": ["科幻世界出版社", "新星出版社", "重庆出版社", "江苏凤凰文艺"],
    },
    "玄幻": {
        "tags": ["玄幻", "修仙", "修真", "魔法", "斗气", "武魂", "穿越", "重生", "异界", "仙侠"],
        "color": "darkblue",
        "authors": ["天蚕土豆", "辰东", "耳根", "忘语", "猫腻", "萧潜", "我吃西红柿"],
        "publishers": ["起点中文", "纵横中文", "创世中文", "阅文集团"],
    },
    "言情": {
        "tags": ["言情", "都市", "校园", "总裁", "穿越", "重生", "甜宠", "虐恋", "古风", "青春"],
        "color": "pink",
        "authors": ["顾漫", "桐华", "匪我思存", "辛夷坞", "八月长安", "顾西爵", "墨宝非宝"],
        "publishers": ["晋江文学", "花火", "魅丽文化", "江苏文艺"],
    },
    "悬疑": {
        "tags": ["悬疑", "推理", "侦探", "犯罪", "恐怖", "惊悚", "心理", "密室", "法医", "破案"],
        "color": "black",
        "authors": ["东野圭吾", "阿加莎", "柯南道尔", "紫金陈", "周浩晖", "雷米", "秦明"],
        "publishers": ["新星出版社", "南海出版公司", "人民文学", "湖南文艺"],
    },
    "历史": {
        "tags": ["历史", "三国", "明朝", "唐朝", "宋朝", "清朝", "战国", "秦汉", "魏晋", "南北朝"],
        "color": "brown",
        "authors": ["当年明月", "二月河", "孙皓晖", "易中天", "蒙曼", "王立群", "袁腾飞"],
        "publishers": ["人民文学", "中华书局", "商务印书馆", "浙江文艺"],
    },
    "文学": {
        "tags": ["文学", "经典", "名著", "散文", "诗歌", "小说", "随笔", "传记", "回忆录", "文集"],
        "color": "beige",
        "authors": ["余华", "莫言", "贾平凹", "王小波", "张爱玲", "沈从文", "钱钟书"],
        "publishers": ["人民文学", "作家出版社", "上海译文", "译林出版社"],
    },
    "经管": {
        "tags": ["管理", "经济", "商业", "金融", "投资", "营销", "创业", "职场", "成功", "理财"],
        "color": "silver",
        "authors": ["彼得·德鲁克", "巴菲特", "瑞·达利欧", "吴晓波", "薛兆丰", "香帅", "刘润"],
        "publishers": ["机械工业", "中信出版社", "湛庐文化", "浙江人民"],
    },
    "科技": {
        "tags": ["科技", "互联网", "编程", "人工智能", "大数据", "云计算", "区块链", "产品", "设计", "创业"],
        "color": "cyan",
        "authors": ["吴军", "万维钢", "采铜", "李开复", "雷军", "周鸿祎", "傅盛"],
        "publishers": ["人民邮电", "电子工业", "机械工业", "中信出版社"],
    },
}

BOOK_TITLES = {
    "科幻": ["三体", "流浪地球", "基地", "沙丘", "银河帝国", "火星救援", "安德的游戏", "神经漫游者", "雪崩", "仿生人会梦见电子羊吗"],
    "玄幻": ["斗破苍穹", "遮天", "凡人修仙传", "诛仙", "将夜", "庆余年", "择天记", "剑来", "诡秘之主", "大主宰"],
    "言情": ["何以笙箫默", "微微一笑很倾城", "步步惊心", "甄嬛传", "致我们终将逝去的青春", "最好的我们", "你好旧时光", "暗恋橘生淮南", "十年一品温如言", "余生请多指教"],
    "悬疑": ["白夜行", "嫌疑人X的献身", "解忧杂货店", "无人生还", "东方快车谋杀案", "福尔摩斯探案集", "隐秘的角落", "长夜难明", "心理罪", "法医秦明"],
    "历史": ["明朝那些事儿", "万历十五年", "大秦帝国", "康熙大帝", "雍正皇帝", "乾隆皇帝", "易中天中华史", "中国通史", "史记", "资治通鉴"],
    "文学": ["活着", "百年孤独", "平凡的世界", "白鹿原", "红高粱", "边城", "围城", "黄金时代", "半生缘", "边城浪子"],
    "经管": ["原则", "穷查理宝典", "卓有成效的管理者", "影响力", "从0到1", "创业维艰", "重新定义公司", "激荡三十年", "经济学原理", "国富论"],
    "科技": ["浪潮之巅", "智能时代", "数学之美", "文明之光", "硅谷之谜", "人工智能", "深度学习", "未来简史", "今日简史", "人类简史"],
}


def generate_books(count: int = 100) -> list:
    books = []
    categories = list(BOOK_CATEGORIES.keys())
    book_id_counter = 1

    for cat_name, cat_info in BOOK_CATEGORIES.items():
        titles = BOOK_TITLES[cat_name]
        for i, title in enumerate(titles):
            author = random.choice(cat_info["authors"])
            publisher = random.choice(cat_info["publishers"])
            tags = random.sample(cat_info["tags"], k=random.randint(3, 6))
            word_count = random.randint(50000, 500000)
            publish_year = random.randint(1990, 2024)
            avg_rating = round(random.uniform(3.0, 5.0), 1)
            borrow_count = random.randint(0, 500)

            book = {
                "book_id": f"b{book_id_counter:04d}",
                "title": title,
                "author": author,
                "publisher": publisher,
                "publish_year": publish_year,
                "category": cat_name,
                "tags": tags,
                "word_count": word_count,
                "cover_color": cat_info["color"],
                "avg_rating": avg_rating,
                "borrow_count": borrow_count,
                "rating_count": random.randint(5, 200),
                "is_new_book": borrow_count == 0,
                "description": f"{title}是一本{cat_name}类小说，由{author}创作，讲述了一个精彩的故事。",
            }
            books.append(book)
            book_id_counter += 1

    extra = count - len(books)
    if extra > 0:
        for _ in range(extra):
            cat_name = random.choice(categories)
            cat_info = BOOK_CATEGORIES[cat_name]
            title = f"{cat_name}小说_{book_id_counter}"
            author = random.choice(cat_info["authors"])
            publisher = random.choice(cat_info["publishers"])
            tags = random.sample(cat_info["tags"], k=random.randint(3, 6))
            word_count = random.randint(50000, 500000)
            publish_year = random.randint(1990, 2024)
            avg_rating = round(random.uniform(3.0, 5.0), 1)
            borrow_count = random.randint(0, 500)

            book = {
                "book_id": f"b{book_id_counter:04d}",
                "title": title,
                "author": author,
                "publisher": publisher,
                "publish_year": publish_year,
                "category": cat_name,
                "tags": tags,
                "word_count": word_count,
                "cover_color": cat_info["color"],
                "avg_rating": avg_rating,
                "borrow_count": borrow_count,
                "rating_count": random.randint(5, 200),
                "is_new_book": borrow_count == 0,
                "description": f"{title}是一本{cat_name}类书籍。",
            }
            books.append(book)
            book_id_counter += 1

    return books


def generate_users(count: int = 50, books: list = None) -> list:
    if not books:
        books = generate_books(80)

    users = []
    occupations = ["学生", "程序员", "教师", "医生", "设计师", "运营", "产品经理", "销售", "工程师", "公务员"]

    for i in range(1, count + 1):
        user_id = f"u{i:04d}"
        username = f"用户{i}"
        age = random.randint(18, 60)
        gender = random.choice(["male", "female", "other"])
        occupation = random.choice(occupations)

        borrow_count = random.randint(0, 30)
        borrow_history = []
        if borrow_count > 0:
            sampled_books = random.sample(books, k=min(borrow_count, len(books)))
            for book in sampled_books:
                read_completion = round(random.uniform(0.0, 1.0), 2)
                read_duration = random.randint(0, 7200)
                rating = round(random.uniform(1.0, 5.0), 1) if random.random() > 0.3 else None
                borrow_num = random.randint(1, 5) if random.random() > 0.8 else 1
                has_comment = random.random() > 0.7

                record = {
                    "book_id": book["book_id"],
                    "borrow_time": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                    "return_time": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat() if random.random() > 0.2 else None,
                    "read_completion": read_completion,
                    "read_duration": read_duration,
                    "rating": rating,
                    "comment": f"这本书{'很' if rating and rating > 4 else '还'}不错" if has_comment else None,
                    "borrow_count": borrow_num,
                }
                borrow_history.append(record)

        ratings = [r["rating"] for r in borrow_history if r["rating"] is not None]
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

        is_new = len(borrow_history) == 0

        interest_tags = []
        if is_new and random.random() > 0.5:
            cat = random.choice(list(BOOK_CATEGORIES.keys()))
            interest_tags = random.sample(BOOK_CATEGORIES[cat]["tags"], k=random.randint(3, 5))

        active_hours = sorted(random.sample(range(24), k=random.randint(2, 6)))

        user = {
            "user_id": user_id,
            "username": username,
            "age": age,
            "gender": gender,
            "occupation": occupation,
            "register_time": (datetime.now() - timedelta(days=random.randint(1, 730))).isoformat(),
            "borrow_history": borrow_history,
            "collections": {},
            "interest_tags": interest_tags,
            "is_new_user": is_new,
            "avg_rating": avg_rating,
            "total_borrow_count": len(borrow_history),
            "active_hours": active_hours,
        }
        users.append(user)

    return users


def main():
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)

    books = generate_books(100)
    users = generate_users(50, books)

    with open(data_dir / "books.json", "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    with open(data_dir / "users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(books)} books")
    print(f"Generated {len(users)} users")
    print(f"Data saved to {data_dir.absolute()}")


if __name__ == "__main__":
    main()

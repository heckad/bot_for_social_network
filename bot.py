import string
from dataclasses import dataclass
from random import randint, choice
from typing import List, Optional

import requests
import configparser

from requests_toolbelt.sessions import BaseUrlSession

config = configparser.ConfigParser()
config.read("config.ini")
config = config["bot"]


@dataclass
class User:
    name: str
    emali: str
    password: str
    token: Optional[str]
    session: Optional[requests.Session]


@dataclass
class Post:
    id: int
    autor: User


def buildblock(size):
    return ''.join(choice(string.ascii_letters) for _ in range(size))


def create_users() -> List[User]:
    users = []
    for _ in range(int(config["number_of_users"])):
        name = buildblock(10)
        user = User(
            name=name,
            emali=f"{name}@mail.ru",
            password="pass",
            token=None,
            session=None
        )

        res = requests.post('http://localhost:8000/api-auth/signup/', json={
            "username": user.name,
            "email": user.emali,
            "password": user.password
        })

        assert res.status_code == 201

        res = requests.post('http://localhost:8000/api-auth/jwt/', json={
            "username": user.name,
            "password": user.password
        })

        assert res.status_code == 200
        user.token = res.json()["token"]
        user.session = BaseUrlSession('http://localhost:8000')
        user.session.headers["Authorization"] = "Bearer {}".format(user.token)

        users.append(user)
    return users


def create_posts(user: User) -> List[Post]:
    posts = []
    for _ in range(randint(0, int(config["max_posts_per_user"]))):
        res = user.session.post('/posts/', {
            "title": f"same title {_}{user.name}",
            "content": f"bla bla {_}"
        })

        assert res.status_code == 201

        posts.append(Post(id=res.json()["id"], autor=user))
    return posts


def create_likes(user: User, all_posts: List[Post]):
    for _ in range(randint(0, int(config["max_likes_per_user"]))):
        res = user.session.post('/likes/', {
            "post": choice(all_posts).id,
            "vote": '+'
        })

        assert res.status_code == 201


def main():
    users = create_users()

    posts = []
    for user in users:
        posts.extend(create_posts(user))

    for user in users:
        create_likes(user, posts)


if __name__ == '__main__':
    main()

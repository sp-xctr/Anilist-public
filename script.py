import colorama
import requests
from secret import *
from flask import Flask, redirect, request
import threading
import webbrowser
import re
import html
from pyfiglet import figlet_format

color = colorama.Fore
red = color.RED
white = color.WHITE
green = color.GREEN
reset = color.RESET
blue = color.BLUE
yellow = color.YELLOW
pink = color.MAGENTA
cyan = color.CYAN
endpoint = "https://graphql.anilist.co"
chosenid = 0
AUTH_CODE = ""
REDIRECT_URL = "http://localhost:5000/callback"

def gradient(text):
    colors = [red, yellow, green, cyan, blue, pink]
    result = ""
    for i, char in enumerate(text):
        result += colors[i % len(colors)] + char
    return result + reset

fquery = '''
query ($search: String) {
  Page(page: 1, perPage: 50) {
    media(search: $search) {
      id
      title {
        romaji
        english
      }
      type
      format
      status
      startDate {
        year
      }
    }
  }
}
'''

save_query = '''
mutation ($mediaId: Int, $progress: Int, $score: Float) {
  SaveMediaListEntry(mediaId: $mediaId, progress: $progress, score: $score) {
    id
    status
    progress
    score
  }
}
'''

view_query = '''
query {
  Viewer {
    id
    name
  }
  MediaListCollection(type: ANIME) {
    lists {
      name
      entries {
        id
        status
        progress
        score
        media {
          title {
            romaji
          }
        }
      }
    }
  }
}
'''

del_query = '''
mutation ($id: Int) {
  DeleteMediaListEntry(id: $id) {
    deleted
  }
}
'''

query = '''
query ($id: Int) {
  Media(id: $id) {
    id
    title {
      romaji
      english
      native
      userPreferred
    }
    source
    popularity
    favourites
    trending
    synonyms
    countryOfOrigin
    isAdult
    nextAiringEpisode {
      airingAt
      episode
      timeUntilAiring
    }
    tags {
      name
      isMediaSpoiler
      rank
    }
    description
    episodes
    duration
    season
    seasonYear
    format
    status
    averageScore
    genres
    coverImage {
      large
    }
    bannerImage
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    studios {
      edges {
        isMain
        node {
          name
        }
      }
    }
    characters {
      edges {
        role
        node {
          name {
            full
          }
        }
      }
    }
    staff {
      edges {
        role
        node {
          name {
            full
          }
        }
      }
    }
    externalLinks {
      site
      url
    }
    trailer {
        id
        site
        thumbnail
    }
    rankings {
        rank
        type
        context
    }
  }
}
'''

app = Flask(__name__)

class Parse():
    def __init__(self, toparse):  
        self.data = toparse["data"]["Media"]

        self.rank = "N/A"
        self.popular = "N/A"

        self.supporting = []
        self.background = []
        self.main = []
        self.studios = []

        self.spoilerTag = []
        self.fullTag = []

        self.romaji= self.data["title"]["romaji"]
        self.english = self.data["title"]["english"]
        self.native = self.data["title"]["native"]

        self.eps = self.data["episodes"]
        self.duration = self.data["duration"]

        self.desc = self.data["description"]
        clean_html = re.sub(r'<br\s*/?>', '', self.desc)
        clean_html = re.sub(r'<[^>]+>', '', clean_html)
        self.desc = html.unescape(clean_html)


        self.coverImage = self.data["coverImage"]["large"]
        self.bannerImage = self.data["bannerImage"]

        self.format = self.data["format"]
        self.status = self.data["status"]

        self.avgscore = self.data["averageScore"]

        self.genres = []
        for genre in self.data["genres"]:
            if genre:
                self.genres.append(genre)

        for tag in self.data["tags"]:
            self.fullTag.append(tag["name"])
            if tag["isMediaSpoiler"]:
                self.spoilerTag.append(tag)

        self.start = f"{self.data["startDate"]["day"]}/{self.data["startDate"]["month"]}/{self.data["startDate"]["year"]}"
        self.end = f"{self.data["endDate"]["day"]}/{self.data["endDate"]["month"]}/{self.data["endDate"]["year"]}"

        self.isAdult = self.data["isAdult"]

        for i in self.data["studios"]["edges"]:
            if i["isMain"]:
                self.mstdio = i["node"]["name"]
            else:
                self.studios.append(i["node"]["name"])

        for atom in self.data["characters"]["edges"]:
            if atom["role"] == "SUPPORTING":
                self.supporting.append(atom["node"]["name"]["full"])
            elif atom["role"] == "BACKGROUND":
                self.background.append(atom["node"]["name"]["full"])
            elif atom["role"] == "MAIN":
                self.main.append(atom["node"]["name"]["full"])

        if self.data["trailer"]["site"] == "youtube":
            self.trailer = f"https://www.youtube.com/watch?v={self.data["trailer"]["id"]}"
            self.trailerThumbnail = self.data["trailer"]["thumbnail"]

        for rank in self.data["rankings"]:
            if rank["context"] == "highest rated all time":
                self.rank = rank["rank"]
            elif rank["context"] == "most popular all time":
                self.popular = rank["rank"]
            else: continue

@app.route("/")
def home():
    return redirect(f"https://anilist.co/api/v2/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URL}&response_type=code")

@app.route("/callback")
def callback():
    global AUTH_CODE
    AUTH_CODE = request.args.get("code")

    if not AUTH_CODE:
        return redirect("http://localhost:5000/notnice")

    token_response = requests.post("https://anilist.co/api/v2/oauth/token", data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URL,
        "code": AUTH_CODE
      })

    if token_response.status_code == 200:
      token_data = token_response.json()
      access_token = token_data["access_token"]
      with open ("token.txt", "w") as f:
          f.write(access_token)
      return redirect("http://localhost:5000/nice")
    else:
      return redirect("http://localhost:5000/notnice")

def get_headers():
  with open ("token.txt") as f:
      ACCESS_TOKEN = f.read().strip()

  headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
  }

  return headers

@app.route("/nice")
def nice():
    return "everything went well"

@app.route("/notnice")
def notnice():
    return "something went wrong"

def runflask():
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

def get_id():
    idlist = []

    search = input("Search: ")

    variables = {
        'search': f"{search}"
    }

    response = requests.post(endpoint, json={'query': fquery, 'variables':variables})
    if response.status_code == 200:
        data = response.json()
        for i, anime in enumerate(data["data"]["Page"]["media"]):
            show_id = anime["id"]
            rtitle = anime["title"]["romaji"]
            etitle = anime["title"]["english"]
            show_type = anime["type"]
            show_format = anime["format"]
            show_status = anime["status"]
            start = anime["startDate"]["year"]
            
            print(f'''{i + 1}. Titles:   Romanji->  {rtitle}
              English->   {etitle}
    Type:     {show_type}
    Format:   {show_format}
    Status:   {show_status}
    Started:  {start}
    Id:       {show_id}
    ''')
            idlist.append(show_id)      
    else:
        print("getting failed", response)

    choice = int(input("Input a number of the anime you want to see (1, 2 ..... X): "))
    chosenid = idlist[choice - 1]

    return chosenid

def View_Entry():
  response = requests.post(endpoint, json={"query": view_query}, headers=get_headers())

  print(response.json())

def Delete_Entry(chosendid):
  vars = {
    "id": chosendid
  }
  
  requests.post(endpoint, json={"variables": vars, "query": del_query}, headers=get_headers())

def Save_Entry(chosenid):
  epsquery = '''
  query ($id: Int) {
    Media(id: $id, type: ANIME) {
      id
      title {
        romaji
      }
      episodes
    }
  }
  '''

  progress_vars = {
      "id": chosenid,
      "query": epsquery
  }

  send = requests.post(endpoint, json=progress_vars, headers=get_headers())
  if send.status_code == 200:
    json = send.json()
    eps = json["data"]["Media"]["episodes"]

    epcount = input("how many eps? ")
    if epcount != "full":
        epcount = int(epcount)
    else:
        epcount = eps
    
    rating = input("Your rating: ")

    private = input("private (y/n): ").lower().strip()
    if private != "y":
        private = False
    else:
        private = True

    variables = {
        "mediaId": chosenid,
        "progress": epcount,
        "score": float(rating),
        "private": private
    }

    final = requests.post(endpoint, json={"variables": variables, "query": save_query}, headers=get_headers())
    if final.status_code == 200:
        print("done")
    else:
        print(f"{final.json()}")
  else:
      print(send.json())

def fetchquery(chosenid):
    variables = {
        'id': chosenid
    }

    response = requests.post(endpoint, json={'query': query, 'variables': variables})

    if response.status_code == 200:
        data = response.json()

        anime1 = Parse(data)

        title = anime1.english or anime1.romaji or "Untitled"
        ascii_title = figlet_format(title, font="slant")
        ascii_title_colored = gradient(ascii_title)

        fabulous = f"""{ascii_title_colored}
        {cyan}┌─ Anime Overview {'─' * (40)}{reset}
        {yellow}│ Title:        {white}{anime1.romaji}
        {yellow}│ English:      {white}{anime1.english}
        {yellow}│ Native:       {white}{anime1.native}
        {yellow}│ Format:       {white}{anime1.format}
        {yellow}│ Status:       {white}{anime1.status}
        {yellow}│ Episodes:     {white}{anime1.eps}
        {yellow}│ Duration:     {white}{anime1.duration} min
        {yellow}│ Start Date:   {white}{anime1.start}
        {yellow}│ End Date:     {white}{anime1.end}
        {yellow}│ Age Rating:   {white}{'18+' if anime1.isAdult else 'All Ages'}
        {yellow}│ Avg Score:    {white}{anime1.avgscore}%
        {yellow}│ Popularity:   {white}#{anime1.popular}
        {yellow}│ Rating Rank:  {white}#{anime1.rank}
        {yellow}│ Studio:       {white}{anime1.mstdio}
        {yellow}│ Other Studios:{white}{", ".join(anime1.studios) or "None"}
        {yellow}│ Genres:       {white}{", ".join([g for g in anime1.genres if g])}
        {yellow}│ Characters:
        {yellow}│   Main:       {white}{", ".join(anime1.main)}
        {yellow}│   Supporting: {white}{", ".join(anime1.supporting)}
        {yellow}│   Background: {white}{", ".join(anime1.background)}
        {yellow}│ Tags:         {white}{", ".join(anime1.fullTag)}
        {yellow}│ Spoiler Tags: {white}{", ".join(tag['name'] for tag in anime1.spoilerTag) or "None"}
        {yellow}│ Trailer:      {white}{anime1.trailer if hasattr(anime1, 'trailer') else "N/A"}
        {cyan}└{'─' * 60}{reset}
        """
        try:
          print(fabulous)
          input("Press enter to end...... ")
        except Exception as e:
            print(e)
            input()
    else:
        print("failed lmao", response)

    return data

def main_cli():
  sdcw = input("Save, Delete or Check? (s, d, c, v)").lower()
  if sdcw == "c":
    fetchquery(get_id())
  elif sdcw == "d":
    Delete_Entry(get_id())
  elif sdcw == "s":
    Save_Entry(get_id())
  elif sdcw == "v":
    View_Entry()

if __name__ == "__main__":
    threading.Thread(target=runflask, daemon=True).start()
    webbrowser.open("http://localhost:5000")

    main_cli()
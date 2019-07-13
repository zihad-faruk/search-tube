# Importing all the built in libraries
import googleapiclient.discovery
from googleapiclient.discovery import build

import os

# To import requests form webpages
# Requests is used to get data form webpages
import requests
from bs4 import BeautifulSoup

# This modules are used for processing the comments
# Importing module for translating comments in different languages
from translate import Translator
# Importing module for sentiment analysis of the comments
from textblob import TextBlob
# Importing module for detecting the language of the comment
from langdetect import detect

# This will autodetect the language of the comment and translate it in English
translator = Translator(from_lang='autodetect', to_lang='en')

# The Global variables needed are Defined here
DEVELOPER_KEY = 'AIzaSyDjB_gvuDVdrRCOW0OLU38NWIa4pSmG4Y4'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
queue = "queue.txt"
crawled = "crawled.txt"
list_of_links = []


# The function is required for using the second
# element of the list to use as the key to sort
# the list
def custom_sort(t):
    return t[1]


# The function will be used for adding elements to
# the list
def add_elements_to_list(t1, t2,t3,t4,t5,t6,t7):
    list_of_links.append((t1, t2,t3,t4,t5,t6,t7))


# Functions for the whole project will be defined here
# Function for detecting the language of the comment
def language_detection(comment):
    result = detect(comment)
    return result


# Function for analyse the sentiment of comments
def english_comment_analysis(comment):
    text_blob_comment = TextBlob(comment)
    if text_blob_comment.sentiment.polarity > 0:
        #print("Postive comment")
        return True
    elif text_blob_comment.sentiment.polarity == 0:
        #print("Neutral Comment")
        pass
    else:
        #print("Negative comment")
        return False


# Function for processing the comments
def comment_proecessor(video_id):
    pos = 0
    neg = 0
    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyDjB_gvuDVdrRCOW0OLU38NWIa4pSmG4Y4"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)

    request = youtube.commentThreads().list(
        part="snippet",
        moderationStatus="published",
        order="relevance",
        videoId=video_id
    )

    # #Bn - xfgcdf7w

    response = request.execute()

    for comm in response.get('items', []):

        comment = comm['snippet']['topLevelComment']['snippet']['textDisplay']

        if (language_detection(comment) == 'en'):
            if (english_comment_analysis(comment)):
                pos = pos + 1
            else:
                neg = neg + 1
        else:
            translation = translator.translate(comment)
            if (english_comment_analysis(translation)):
                pos = pos + 1
            else:
                neg = neg + 1
    return pos-neg

# Function for creating the queued and crawled files
def create_data_files():
    write_file(queue, '')
    write_file(crawled, '')


# Function for creating a new file
def write_file(path, data):
    f = open(path, 'w')
    f.write(data)
    f.close()


# Function for appending links to existing files
def append_to_file(path, data):
    with open(path, 'a') as file:
        file.write(data + '\n')


# Function for clearing the files after crawling
def delete_file_contents(path):
    with open(path, 'w'):
        pass


def thumbnail_finder(video_id):
    DEVELOPER_KEY = "AIzaSyDjB_gvuDVdrRCOW0OLU38NWIa4pSmG4Y4"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"


    youtube = googleapiclient.discovery.build(
        api_service_name, api_version,  developerKey=DEVELOPER_KEY)

    request = youtube.videos().list(
        part="snippet",
        id= video_id
    )
    response = request.execute()
    for thumb in response.get('items', []):
        thum = thumb['snippet']['thumbnails']['high']['url']

    return thum

def view_count_finder(video_Id):
    DEVELOPER_KEY = "AIzaSyDjB_gvuDVdrRCOW0OLU38NWIa4pSmG4Y4"
    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)

    request = youtube.videos().list(
        part="statistics",
        id=video_Id
    )
    response = request.execute()

    for view in response.get('items', []):
        view_count = view['statistics']['viewCount']

    return view_count


# Function for reading links stored in queue file
# Then the url is crawled
# def read_queue_file(file_name):
# with open(file_name,'rt') as f:

##for line in f:
# crawl_data(line)


# The function will be used to count the points of
# each video
def point_counter(likes, dislikes, views, comment_points):
    like_points = int(likes) * 1
    dislike_points = int(dislikes) * 1
    view_points = int(views) * .5
    total_comment_points = int(comment_points) * 1

    result = like_points - dislike_points + round(view_points) + total_comment_points
    return result


# The function for getting search data from youtube
# The retrieved data will be stored in file then
# ready for crawling
def youtube_search(search_term):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    search_response = youtube.search().list(
        q=search_term,
        part='id,snippet',
        maxResults=3,
        order='rating'

    ).execute()

    videos = []

    # Creating the files needed for further crawling
    create_data_files()

    # function of get is used to collect items for the search term
    # the parameter values of items can be found in the website
    # the another parameter in get is used as default
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append('%s (%s)' % (search_result['snippet']['title'],
                                       search_result['id']['videoId']))

        video_Id = search_result['id']['videoId']
        # For making the url readable and use it to crawl data
        base_url = "https://www.youtube.com/watch?v=" + search_result['id']['videoId']

        # Append links to the file
        append_to_file(queue, base_url)
        crawl_data(base_url, video_Id)


# The function for crawling data
def crawl_data(url, video_Id):
    total_views = 0
    total_likes = 0
    total_dislikes = 0

    # To get the contents of the url
    source_code = requests.get(url)
    plain_text = source_code.text

    # Creating the beautifulsoup object for using
    # the functionalities of beautifulsoup
    soup = BeautifulSoup(plain_text, 'html.parser')

    # Findall is used to go and find all the data in source code

    for vid_title in soup.find_all('h1'):
        print(vid_title.text)

    for like in soup.find_all('button',
                              class_='yt-uix-button yt-uix-button-size-default yt-uix-button-opacity yt-uix-button-has-icon no-icon-markup like-button-renderer-like-button like-button-renderer-like-button-unclicked yt-uix-clickcard-target yt-uix-tooltip'):
        total_likes = like.text
        print(total_likes)

    for dislike in soup.find_all('button',
                                 class_='yt-uix-button yt-uix-button-size-default yt-uix-button-opacity yt-uix-button-has-icon no-icon-markup like-button-renderer-dislike-button like-button-renderer-dislike-button-unclicked yt-uix-clickcard-target yt-uix-tooltip'):
        total_dislikes = dislike.text
        print(total_dislikes)

    total_views = view_count_finder(video_Id)
    total_comment_points = comment_proecessor(video_Id)
    print(total_views)
    print(total_comment_points)
    total_points = point_counter(total_likes, total_dislikes, total_views, total_comment_points)
    print(total_points)
    thumb = thumbnail_finder(video_Id)
    add_elements_to_list(video_Id,total_points,total_likes,total_dislikes,total_views,vid_title.text,thumb)
    # For sorting the list
    list_of_links.sort(key=custom_sort, reverse=True)
    print(list_of_links)



# Calling the main function
def main():
    youtube_search("python")
    # read_queue_file(queue)


main()

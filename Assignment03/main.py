from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token;
from google.auth.transport import requests
from google.cloud import firestore, storage
import starlette.status as status
from datetime import datetime
import local_constants
import io
import base64


app = FastAPI()

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()

app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")

def getUser(user_token):
    user = firestore_db.collection('users').document(user_token['user_id'])
    return user

def getTweets(user):
    tweet_ref = firestore_db.collection('Tweet').order_by('date', direction='DESCENDING').get()
    tweets=[]
    follows=user.get('follows')
    i=0
    for doc in tweet_ref:
        if i==21:
            break
        oneTweet = doc.to_dict()
        for j in follows:
            if oneTweet.get('username')==j:
                tweets.append(oneTweet)
                i = i+1
        if oneTweet.get('username') == user.get('name'):
            tweets.append(oneTweet)
            i = i+1
    return tweets
    


def validateFirebaseToken(id_token):
    if not id_token:
        return None
    
    user_token = None
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token,firebase_request_adapter)
    except ValueError as err:
        print(str(err))

    return user_token

def addFile(file):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    print(file)
    blob = storage.Blob(file.filename, bucket)
    blob.upload_from_file(file.file)
    return blob.public_url

# def downloadBlob(filename):
#     storage_client = storage.Client(project=local_constants.PROJECT_NAME)
#     bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

#     blob = bucket.get_blob(filename)
#     return blob.download_as_bytes()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None
    user = None

    user_token = validateFirebaseToken(id_token)
    print(user_token)
    if not user_token:
        return templates.TemplateResponse('main.html',{'request': request,'user_token':None,'error_message': None, 'user_info':None})
    
    user = getUser(user_token).get()
    
    if not user.exists:
        user=None
    serachTweets = []
    serachUsers=[]
    allTweets=[]
    if user!=None:
        allTweets = getTweets(user)
    return templates.TemplateResponse('main.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user, 'tweets_list':serachTweets,'search_users':serachUsers,'all_tweets':allTweets})


@app.post("/set-user", response_class=RedirectResponse)
async def setUser(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
# pull the form containing our data
    form = await request. form()

    user_doc_ref = firestore_db.collection('users').get()
    for doc in user_doc_ref:
        oneUser = doc.to_dict()
        if oneUser.get('name') == form['userName']:
            return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

    user = firestore_db.collection('users').document(user_token['user_id'])
    if not user.get().exists:
        user_data = {
            'name': form['userName'],
            'tweet_ref': [],
            'follows':[]
        }
        firestore_db.collection('users').document(user_token['user_id']).set(user_data)

# when finished return a redirect with a 302 to force a GET verb
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

# route that will take in an address form and will add it to the firestore and link it to a user
# this will use a new firebase document and reference to connect it to the user
@app.post("/add-tweet", response_class=RedirectResponse)
async def addTweet(request: Request):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request.form()
    src = ''
    if form['file_name'].filename != '':
        src = addFile(form['file_name'])
# create a reference to an  object note that we have not given an ID here
# we are asking firestore to create an ID for us
    tweet_ref = firestore_db.collection('Tweet').document ()
        
# set the data on the address object
    tweet_ref.set({
        'username': form['userName'],
        'date': datetime.now(),
        'content': form['content'],
        'tweetid':tweet_ref.id,
        'img_src':src
    })

    user = getUser(user_token)
    tweets_ref_array = user.get().get('tweet_ref')
    tweets_ref_array.insert(0, tweet_ref)
    user. update({'tweet_ref': tweets_ref_array})

# when finished return a redirect with a 302 to force a GET verb
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

@app.post("/search-user", response_class=RedirectResponse)
async def searchUser(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    error_message = None
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request. form()

    user_doc_ref = firestore_db.collection('users').get()
    serachUsers=[]
    for doc in user_doc_ref:
        oneUser = doc.to_dict()
        if oneUser.get('name').startswith(form['name']):
            serachUsers.append(oneUser)
            

    user = getUser(user_token).get()
    if not user.exists:
        user=None
    serachTweets = []
    allTweets = getTweets(user)
    return templates.TemplateResponse('main.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user, 'tweets_list':serachTweets, "search_users":serachUsers,'all_tweets':allTweets})


@app.post("/search-content", response_class=RedirectResponse)
async def searchContent(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    error_message = None
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request. form()

    tweet_doc_ref = firestore_db.collection('Tweet').get()
    serachTweets=[]
    for doc in tweet_doc_ref:
        oneTweet = doc.to_dict()
        if oneTweet.get('content').startswith(form['content']):
            serachTweets.append(oneTweet)
            

    user = getUser(user_token).get()
    if not user.exists:
        user=None
    serachUsers = []
    allTweets = getTweets(user)
    return templates.TemplateResponse('main.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user, 'tweets_list':serachTweets, "search_users":serachUsers,'all_tweets':allTweets})


#profile view
@app.get("/view-profile", response_class=RedirectResponse)
async def viewProfile(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    error_message = None
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    search=request.query_params.get('viewname')

    userProfile=None
    user_doc_ref = firestore_db.collection('users').get()
    for doc in user_doc_ref:
        oneUser = doc.to_dict()
        if oneUser.get('name') == search:
            userProfile = oneUser
    
    userTweets = []
    tweets = userProfile.get('tweet_ref')
    i =0
    for tweet in tweets:
            if tweet.get().get('content') !=None:
                userTweets.append(tweet.get())
                i = i+1
                if i == 10:
                    break
    
    user = getUser(user_token).get()
    if not user.exists:
        user=None
    
    #Checking follow
    follow = False
    follow_list = user.get('follows')
    for i in follow_list:
        if i == search:
            follow = True
    
    return templates.TemplateResponse('profile.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user, 'user_profile': userProfile, 'tweets_list': userTweets, 'follow_status':follow})

@app.post("/follow", response_class=RedirectResponse)
async def follow(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    error_message = None
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request.form()
    search= form['viewname']

    userProfile=None
    user_doc_ref = firestore_db.collection('users').get()
    for doc in user_doc_ref:
        oneUser = doc.to_dict()
        if oneUser.get('name') == search:
            userProfile = oneUser
    
    userTweets = []
    tweets = userProfile.get('tweet_ref')
    i =0
    for tweet in tweets:
        if tweet.get().get('content') !=None:
            userTweets.append(tweet.get())
            i = i+1
            if i == 10:
                break

    
    #Following user
    userDoc = getUser(user_token)
    follow_ref_array = userDoc.get().get('follows')
    follow_ref_array.insert(0, form['viewname'])
    userDoc.update({'follows': follow_ref_array})


    user = getUser(user_token).get()
    if not user.exists:
        user=None

    

    #Checking follow
    follow = False
    follow_list = user.get('follows')
    for i in follow_list:
        if i == search:
            follow = True
    
    
    return templates.TemplateResponse('profile.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user, 'user_profile': userProfile, 'tweets_list': userTweets, 'follow_status':follow})

@app.post("/unfollow", response_class=RedirectResponse)
async def unfollow(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    error_message = None
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request.form()
    search= form['viewname']

    userProfile=None
    user_doc_ref = firestore_db.collection('users').get()
    for doc in user_doc_ref:
        oneUser = doc.to_dict()
        if oneUser.get('name') == search:
            userProfile = oneUser
    
    userTweets = []
    tweets = userProfile.get('tweet_ref')
    i =0
    for tweet in tweets:
        if tweet.get().get('content') !=None:
            userTweets.append(tweet.get())
            i = i+1
            if i == 10:
                break

    #Unfollow user
    userDoc = getUser(user_token)
    follow_ref_array = userDoc.get().get('follows')
    follow_ref_array.remove(form['viewname'])
    userDoc.update({'follows': follow_ref_array})

    
    user = getUser(user_token).get()
    if not user.exists:
        user=None

    

    #Checking follow
    follow = False
    follow_list = user.get('follows')
    for i in follow_list:
        if i == search:
            follow = True
    
    
    return templates.TemplateResponse('profile.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user, 'user_profile': userProfile, 'tweets_list': userTweets, 'follow_status':follow})

@app.post("/edit-tweet-page", response_class=RedirectResponse)
async def editPage(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    error_message=None
# pull the form containing our data
    form = await request. form()
    tweetid = form['id']
    
    tweet_doc_ref = firestore_db.collection('Tweet').get()
    tweetFound={}
    for doc in tweet_doc_ref:
        oneTweet = doc.to_dict()
        if oneTweet.get('tweetid') == tweetid:
            tweetFound = oneTweet

# when finished return a redirect with a 302 to force a GET verb
    return templates.TemplateResponse('edit-tweet.html',{'request': request,'user_token': user_token,'error_message': error_message, 'tweet':tweetFound})


@app.post("/edit-tweet", response_class=RedirectResponse)
async def editTweet(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    error_message=None
# pull the form containing our data
    form = await request. form()
    tweetid = form['id']
    src = ''
    if form['file_name'].filename != '':
        src = addFile(form['file_name'])
    
    tweet_doc_ref = firestore_db.collection('Tweet').where('tweetid','==', tweetid).get()
    for doc in tweet_doc_ref:
        oneTweet = doc.to_dict()
        tweeting_id = doc.id
        oneTweet['content']=form['content']
        if src != '':
            oneTweet['img_src']=src
        firestore_db.collection('Tweet').document(tweeting_id).set(oneTweet)
    
# when finished return a redirect with a 302 to force a GET verb
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

@app.post("/delete-tweet", response_class=RedirectResponse)
async def deleteTweet(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    error_message=None
# pull the form containing our data
    form = await request. form()
    tweetid = form['id']
    
    tweet_doc_ref = firestore_db.collection('Tweet').where('tweetid','==', tweetid).get()
    for doc in tweet_doc_ref:
    # Delete each document
        doc.reference.delete()
    
# when finished return a redirect with a 302 to force a GET verb
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)




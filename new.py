from bs4 import BeautifulSoup as bs
import streamlit as st
import pandas as pd
from textblob import TextBlob
from pytube import YouTube
import requests
from pytube import Search


headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.1000.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com",
    }
ctr=1

base_url='https://www.imdb.com/search/title/?title_type=feature'

genres=['action', 'adventure', 'comedy', 'family', 'history', 'crime', 'fantasy',
         'horror', 'news', 'reality-tv', 'short', 'sport', 'animation', 'biography', 
         'documentary', 'film-noir', 'drama', 'game-show', 'music', 'romance', 'talk-show', 
         'musical', 'mystery', 'sci-fi', 'thriller', 'war', 'western']


def main():
    global ctr
    st.title('Movie Recommendation System')
    # Sidebar for filters
    st.sidebar.title('Filters')

    selected_type = st.sidebar.selectbox('Select Media Type', ['Movies', 'Web Series'], index=0)
    if selected_type =='Web Series':
        ctr=0


    selected_genres = st.sidebar.multiselect('Select Genre', genres)
    
    # Date range input
    min_date = [st.sidebar.date_input('Minimum Release Date')]
    max_date = [st.sidebar.date_input('Maximum Release Date')]
    search_button = st.sidebar.button('Search')
    df=pd.read_csv('new.csv')
    if 'duration' in list(df.columns):
        ctr=1
    else:
        ctr=0
    display(df.iloc[:6,:])

    if search_button:
        st.write('Scraping data from IMDb...')
        new_data = scrape(selected_type,selected_genres,min_date,max_date)
        st.write('Scraping complete!')
        st.write(new_data)



def scrape(selected_type,selected_genres,min_date,max_date):
    import pandas as pd
    df=pd.DataFrame(columns=['movie_title','year','stars','duration','rating'])
    # df.columns=['movie_title','year','stars','duration','rating']
    if selected_type=='Web Series':
        url='https://www.imdb.com/search/title/?title_type=tv_series'
        main_class='sc-ab6fa25a-3 bVYfLY dli-parent'
        ctr=0
    else:
        url=base_url
        main_class='sc-d80c3c78-4 kXzHjH dli-parent'
    if len(selected_genres)>0:
        url+='&genres='+','.join(selected_genres)
    if len(min_date)>0:
        url+='&release_date='+str(min_date[0])
    if len(max_date)>0:
        url+=','+str(max_date[0])

    resp=requests.get(url,headers=headers)
    soup=bs(resp.content,'html.parser')

    print(url)
    rows=[]
    main_divs=soup.find_all('div',class_=main_class)
    print('length is ',len(main_divs))
    # try:
    for sop in main_divs:
        try:
            movie_link=sop.find('a',class_="ipc-title-link-wrapper")
            stars= float(sop.find('span',class_='ipc-rating-star ipc-rating-star--base ipc-rating-star--imdb ratingGroup--imdb-rating').text.split()[0])
            movie_title=sop.find('h3',class_='ipc-title__text').text.split('.')[1].strip()
            meta=[i.text for i in sop.find('div',class_='sc-b0691f29-7 hrgukm dli-title-metadata').find_all('span')]
            id=movie_link['href'].split('/')[2]
            #image link
            rem_num=bs(requests.get('https://www.imdb.com'+movie_link['href'],headers=headers).content,'html.parser').find('a',class_='ipc-lockup-overlay ipc-focusable')['href'].split('/')[-2]
            image_sub ='https://www.imdb.com/title/'+str(id)+'/mediaviewer/'+str(rem_num)+'/?ref_=tt_ov_i'
            image_url=bs(requests.get(image_sub,headers=headers).content,'html.parser').find('div',class_='sc-7c0a9e7c-2 ghbUKT').find('img')['src']

            #video link
            # video_url=bs(requests.get('https://www.imdb.com'+movie_link['href'],headers=headers).content,'html.parser').find('video',class_='jw-video jw-reset')['src']

            # sentiment analysis
            latest_review_url='https://www.imdb.com/title/'+id+'/reviews?sort=submissionDate&dir=desc&ratingFilter=0'
            review_soup=bs(requests.get(latest_review_url).content,'html.parser')
            latest_reviews=[i.text for i in review_soup.find_all('div',class_='text show-more__control')]
            net=[TextBlob(review).sentiment.polarity for review in latest_reviews]
            avg_polarity = sum(net)/len(net)
            
            avg_polarity=(((avg_polarity - -1) * 10) / 2) + 0

            if selected_type!='Web Series':
                rows.append([movie_title,meta[0].strip(),stars,meta[1].strip(),meta[2].strip(),avg_polarity,image_url,get_trailer_url(movie_title)])
            else:
                rows.append([movie_title,meta[0].strip(),stars,meta[1].strip(),avg_polarity,image_url,get_trailer_url(movie_title)])
            print(rows)
        except:
            print(main_divs.index(sop))
            pass
    if selected_type!='Web Series':
        df=pd.DataFrame(data =rows,columns=['movie_title','year','stars','duration','rating','avg_polarity','img_url','trailer_url'])
    else:
        df=pd.DataFrame(data =rows,columns=['movie_title','year','stars','rating','avg_polarity','img_url','trailer_url'])
    df['ordering']=0.8*df['stars']+0.2*df['avg_polarity']
    df.sort_values('ordering',ascending=0,inplace=True)
    df['ordering']=round(df['ordering'],2)
    df.to_csv('new.csv')
    display(df.iloc[:5,:])
    # print(new_row,df)
    print(df)
    return url

def display(df):
    global ctr
    if df.shape[1]!=0:
        # Display movie details
        for index, row in df.iterrows():
            # Define CSS style for the movie box
            box_style = """
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                display: flex;
                flex-direction: row;
                align-items: center;
            """

            # Define CSS style for the image
            image_style = """
                max-width: 30%;
                height: auto;
                margin-right: 20px;
            """

            # Define CSS style for the video
            video_style = """
                width: auto;
                height: auto;
            """

            # Define HTML content for the movie box
            if ctr==1:
                box_content = f"""
                    <div style="{box_style}">
                        <img src="{row['img_url']}" alt="{row['movie_title']}" style="{image_style}">
                        <div>
                            <h3 style="font-weight: bold;">{row['movie_title']} ({row['year']})</h3>
                            <p><strong>Stars:</strong> {row['stars']} | <strong>Duration:</strong> {row['duration']} | <strong>Rating:</strong> {row['rating']}</p>
                            <iframe width="750" height="270" src="{row['trailer_url']}" frameborder="0" allowfullscreen style="{video_style}"></iframe>
                        </div>
                    </div>
                """
            else:
                box_content = f"""
                    <div style="{box_style}">
                        <img src="{row['img_url']}" alt="{row['movie_title']}" style="{image_style}">
                        <div>
                            <h3 style="font-weight: bold;">{row['movie_title']} ({row['year']})</h3>
                            <p><strong>Stars:</strong> {row['stars']} | <strong>Rating:</strong> {row['rating']}</p>
                            <iframe width="750" height="270" src="{row['trailer_url']}" frameborder="0" allowfullscreen style="{video_style}"></iframe>
                        </div>
                    </div>
                """
            # Display the movie box using st.markdown()
            st.markdown(box_content, unsafe_allow_html=True)
    else:
        st.write('No Movies found for this filter!!')

def get_trailer_url(movie_title):
    return 'https://www.youtube.com/embed/'+str(Search(movie_title+str('movie trailer')).results[0].video_id)+'?autoplay=1'
    


if __name__ == '__main__':
    main()
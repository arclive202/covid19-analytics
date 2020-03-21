import pandas as pd
import plotly.express as px
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.animation as animation
from IPython.display import HTML
from matplotlib import cm
from lxml import html
from bs4 import BeautifulSoup

def refine(covid_df):
    covid_refined_pdf=covid_df.melt(id_vars=["Province/State", 
                     "Country/Region","Lat","Long"], 
                      var_name="Date", 
                      value_name="Value")

    covid_refined_pdf=covid_refined_pdf.drop(columns=['Province/State','Lat','Long']) \
        .groupby(['Country/Region','Date']).sum() \
        .reset_index(drop=False) \
        .rename(columns={"Country/Region": "Country"})

    covid_refined_pdf['DateTime']=pd.to_datetime(covid_refined_pdf['Date'])
    covid_refined_pdf['Date']= \
              covid_refined_pdf['DateTime'].dt.strftime('%m/%d/%y')


    covid_refined_pdf=covid_refined_pdf \
                       .sort_values(by=['Country', 'DateTime'])

    covid_refined_pdf['Country'].mask(covid_refined_pdf['Country'] \
                        == 'US', 'United States', inplace=True)
    covid_refined_pdf['Country'].mask(covid_refined_pdf['Country'] \
                        == 'Korea, South','South Korea', inplace=True)
    covid_refined_pdf['Country'].mask(covid_refined_pdf['Country'] \
                        == 'Taiwan*', 'Taiwan', inplace=True)
    
    return covid_refined_pdf
    
def ingest():
  confirmed_ts_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv'
  covid_confirmed_df = pd.read_csv(confirmed_ts_url)
  deaths_ts_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv'
  covid_deaths_df = pd.read_csv(deaths_ts_url)
  recovered_ts_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv'
  covid_recovered_df = pd.read_csv(recovered_ts_url)
  covid_confirmed_pdf=refine(covid_confirmed_df)
  covid_deaths_pdf=refine(covid_deaths_df)
  covid_recovered_pdf=refine(covid_recovered_df)
  covid_pdf = covid_confirmed_pdf.merge(covid_deaths_pdf[['Country', 'Date','Value']], how='inner', left_on=['Country', 'Date'], right_on=['Country','Date'])
  covid_pdf = covid_pdf.merge(covid_recovered_pdf[['Country', 'Date','Value']], how='inner', left_on=['Country', 'Date'], right_on=['Country','Date'])
  covid_pdf = covid_pdf.rename(columns={"Value_x": "Confirmed","Value_y":"Deaths","Value":"Recovered"})
  return covid_pdf

def refine_v2(covid_df):
    covid_refined_pdf=covid_df.melt(id_vars=["Province/State", 
                     "Country/Region","Lat","Long"], 
                      var_name="Date", 
                      value_name="Value")

    covid_refined_pdf=covid_refined_pdf.rename(columns={'Province/State':'State'}) \
        .rename(columns={"Country/Region": "Country"}) \
        .groupby(['Country','State','Date']).sum() \
        .reset_index(drop=False) 
        
    covid_refined_pdf['DateTime']=pd.to_datetime(covid_refined_pdf['Date'])
    covid_refined_pdf['Date']= \
              covid_refined_pdf['DateTime'].dt.strftime('%m/%d/%y')


    covid_refined_pdf=covid_refined_pdf \
                       .sort_values(by=['Country', 'DateTime'])

    covid_refined_pdf['Country'].mask(covid_refined_pdf['Country'] \
                        == 'US', 'United States', inplace=True)
    covid_refined_pdf['Country'].mask(covid_refined_pdf['Country'] \
                        == 'Korea, South','South Korea', inplace=True)
    covid_refined_pdf['Country'].mask(covid_refined_pdf['Country'] \
                        == 'Taiwan*', 'Taiwan', inplace=True)
    
    return covid_refined_pdf

def ingest_refine_v2():
    us_covid_pdf = pd.read_csv('https://query.data.world/s/mszgcko2hys36laqy7rlcfm6nnptwx')
    us_covid_pdf = us_covid_pdf.pivot_table(
            values='Cases', 
            index=['Date', 'Country_Region','Province_State'], 
            columns='Case_Type', 
            aggfunc=np.sum).reset_index(drop=False)

    us_covid_pdf = us_covid_pdf[us_covid_pdf['Country_Region']=='US']

    states_centroids_url="https://developers.google.com/public-data/docs/canonical/states_csv"
    states_centroids_df=pd.read_html(states_centroids_url)[0]
    us_covid_pdf=us_covid_pdf.merge(states_centroids_df[['state','name','latitude','longitude']], how='inner', left_on=['Province_State'], right_on=['name'])
    us_covid_pdf['DateTime'] =pd.to_datetime(us_covid_pdf.Date)
    us_covid_pdf['Date']= \
                  us_covid_pdf['DateTime'].dt.strftime('%m/%d/%y')

    us_covid_pdf = us_covid_pdf.sort_values(['DateTime','Confirmed'],ascending=[True,False]).groupby('Date').head(50).reset_index()
    return us_covid_pdf  

def get_covid_ts_no_china(covid_pdf):
  covid_no_chi_pdf=covid_pdf[covid_pdf['Country']!='China' ]. \
            sort_values(['DateTime','Confirmed'],ascending=[True,False]).groupby('Date').head(50)
  return covid_no_chi_pdf

def get_covid_ts(covid_pdf):
  country_centroids_url="https://developers.google.com/public-data/docs/canonical/countries_csv"
  country_centroids_df=pd.read_html(country_centroids_url)[0]
  covid_pdf = covid_pdf.sort_values(['DateTime','Confirmed'],ascending=[True,False]).groupby('Date').head(50)
  covid_lat_long_pdf=covid_pdf.merge(country_centroids_df[['country','name','latitude','longitude']], how='inner', left_on=['Country'], right_on=['name'])
  return covid_lat_long_pdf
  
def draw_barchart(current_key,key_name,value_name,grp_key_name,df,top_count,title):
    palette='tab20'
    if top_count<=10: 
        palette='tab10' 
    elif top_count<=20: 
        palette='tab20' 
    else: 
        palette='hsv'
    ccolors = cm.get_cmap(palette)(np.arange(top_count, dtype=int))
    dff = df[df[key_name].eq(current_key)].sort_values(by=value_name, ascending=True).tail(top_count)
    ax.clear()
    ax.barh(dff[grp_key_name], dff[value_name], color=ccolors)
    dx = dff[value_name].max() / 200
    for i, (value, name, grp_name) in enumerate(zip(dff[value_name], dff[grp_key_name],dff[key_name])):
        ax.text(value-dx, i,     name,           size=14, weight=600, ha='right', va='bottom')
        ax.text(value-dx, i-.25, grp_name, size=10, color='#444444', ha='right', va='baseline')
        ax.text(value+dx, i,     f'{value:,.0f}',  size=14, ha='left',  va='center')
    ax.text(1, 0.4, current_key, transform=ax.transAxes, color='#777777', size=46, ha='right', weight=800)
    ax.text(0, 1.06, 'Confirmed Count', transform=ax.transAxes, size=12, color='#777777')
    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    ax.xaxis.set_ticks_position('top')
    ax.tick_params(axis='x', colors='#777777', labelsize=12)
    ax.set_yticks([])
    ax.margins(0, 0.01)
    ax.grid(which='major', axis='x', linestyle='-')
    ax.set_axisbelow(True)
    ax.text(0, 1.15, title,
            transform=ax.transAxes, size=24, weight=600, ha='left', va='top')
    ax.text(1, 0, 'by @pradeepreddy;', transform=ax.transAxes, color='#777777', ha='right',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='white'))
    plt.box(False)

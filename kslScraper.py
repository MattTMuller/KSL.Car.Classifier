# -*- coding: utf-8 -*-
"""
Created on Mon Dec 23 23:19:26 2019

@author: Todd
"""

#%%

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re
from re import sub
import pandas as pd
import itertools
import numpy as np
import time

start_time = time.time()

def scrapeForMPG(year, make, model, domain='https://www.edmunds.com/'):
    url = domain+make+'/'+model+'/'+year+'/mpg/'
    #print(url)
    req = Request(url, headers = {'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req)
    bs = BeautifulSoup(webpage, 'html.parser')
    mileage = bs.find('div',{'class','epa-mpg heading-1 font-weight-bold mb-0_25'})
    return float(re.search(('\d+'), mileage.get_text()).group(0))

def scrapeViewAndFavoriteCount(url):
    req = Request(url, headers= {'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req)
    bs = BeautifulSoup(webpage, 'html.parser')
    values = bs.findAll('span', attrs = {'class' : 'vdp-info-value'})
    viewsCount = float(re.search('(\d+)',values[1].get_text()).group(1))
    favoriteCount = float(re.search('(\d+)',values[2].get_text()).group(1))
    return viewsCount, favoriteCount


#%%

carNames, carPrices, carMilages, carMPG, listingLinks = [], [], [], [], []
carMakes, carModels, carYears = [], [], []
carDescriptions = []
carLinks = []
rejects = []
carViewsCount, carFavoriteCount = [], []

#246
for i in range(0,245):
    print(i)
    url = 'https://cars.ksl.com/search/index?p=&mileageFrom=40000&mileageTo=160000&sellerType[]=For%20Sale%20By%20Owner&page=' + str(i)
    req = Request(url, headers = {'User-Agent': 'Mozilla/5.0'})
    
    webpage = urlopen(req)
    bs = BeautifulSoup(webpage, 'html.parser')
    
    listName = bs.findAll('div',{'class','title'},{'a class'})
    listPrices = bs.findAll('div',{'class','listing-detail-line price'})
    listMilages = bs.findAll('div',{'class','listing-detail-line mileage'})
    scrapedLinks = bs.findAll('div', attrs = {'class' : 'title'})
    links = [div.a for div in scrapedLinks]
    listDescriptions = bs.findAll('div',{'class','listing-detail-line srp-listing-description'})

    
    
    for (name, price, miles, link, description) in itertools.zip_longest(listName, listPrices, listMilages,links, listDescriptions):
        try:
            n = re.search('(\d.+)', name.get_text()).group(0)
            
            year = re.search('(\d){4}', n).group(0)
            
            make = re.search('\d+\s(\w+)', n).group(1)
                
            #print(make)
            model = re.search('\d+\s\w+\s(\w+-\d+|\w+)', n).group(1)
            
            #print(model)
            mpg = scrapeForMPG(year = year, make = make, model = model)
            
            p = float(sub(r'[^\d.]', '', price.get_text()))
            m = int(sub(r'[^\d.]', '', miles.get_text()))
            
            l = 'https://cars.ksl.com'+ link['href']
            
            describe = re.sub(r'[\n]|[^\w]', ' ',description.get_text())
            
            viewCount, favoriteCount = scrapeViewAndFavoriteCount(l)
            
            carYears.append(year)
            carMakes.append(make)
            carModels.append(model)
            carNames.append(n)
            carPrices.append(p)
            carMilages.append(m)
            carMPG.append(mpg)
            listingLinks.append(l)
            carDescriptions.append(describe)
            carViewsCount.append(viewCount)
            carFavoriteCount.append(favoriteCount)
        except:
            rejects.append(n)
            continue
        
        
#%%
averageGasPrice = 2.75
carLife = 200000
expectedAnnaulMiles = 7000
loanInterestRate = 0.0424
availableMoney = 4000


d = {'Car':carNames,'Make':carMakes,'Model':carModels , 'Year': carYears,  'Price':carPrices, 'Milage':carMilages, 'MPG':carMPG}

kslCarList = pd.DataFrame(data=d)

galPerYear =  expectedAnnaulMiles / kslCarList['MPG']
annualFuelCost = galPerYear * averageGasPrice
approximateLife = (carLife - expectedAnnaulMiles)/kslCarList['Milage']

requiredCarLoan = []

for cost in kslCarList['Price']:
    if(cost - availableMoney>0):
        requiredCarLoan.append(cost - availableMoney)
    else:
        requiredCarLoan.append(0)
requiredCarLoan = np.array(requiredCarLoan)

totalLoanInterestCost = requiredCarLoan*(1+loanInterestRate/12)**12-requiredCarLoan

pvCost = kslCarList['Price']+totalLoanInterestCost+annualFuelCost*approximateLife
costPerMile = pvCost/(carLife-kslCarList['Milage'])

kslCarList['Expected Car Life (Yr)'] = approximateLife
kslCarList['Gas Cost Per Year'] = annualFuelCost
kslCarList['Loan'] = requiredCarLoan
kslCarList['Cost Per Mile'] = costPerMile
kslCarList['Cost Per Year'] = pvCost/approximateLife
kslCarList['Views Count'] = carViewsCount
kslCarList['Favorite Count'] = carFavoriteCount
kslCarList['Favorite to Views Ratio'] = kslCarList['Favorite Count']/kslCarList['Views Count']
kslCarList['Link'] = listingLinks
kslCarList['Description'] = carDescriptions
kslCarList = kslCarList.sort_values(by='Cost Per Mile')

#Write a supervised learning classifier algorithm that determins if the car is a good value vehicle or not
# Have classifierr look at discription and other aspects of the vehicle




kslCarList.to_csv('C:\\Users\\Todd\\Documents\\Personal Projects\\KSL Car Scraper\\Car List.csv')

print("--- %s seconds ---" % (time.time() - start_time))
    
#expeted miles left in the car
#input of miles driven per year
#number of years you can expect to be able to drive the car
#cost per year to own the vehicle (liability insurance)

#Resource Used
#https://stackoverflow.com/questions/875968/how-to-remove-symbols-from-a-string-with-python
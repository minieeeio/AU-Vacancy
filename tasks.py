import os
import re
import time

from pathlib import Path

import requests
from robocorp import browser
from robocorp.tasks import task
from RPA.Browser.Playwright import Playwright
from RPA.Desktop import Desktop
from RPA.Tables import Tables
from bs4 import BeautifulSoup




from urllib.parse import urljoin


from db import get_connection, save_result, build_report, now

from gmail import get_credentials, send_email

conn = get_connection()
run_started = now()





AUS_BANK="https://www.thinkingaustralia.com/finance/australian-banks/"
AUS_INSURANCE="https://insurancecouncil.com.au/industry-members/members-and-member-brands/"
AUS_FINTECH="https://ensun.io/search/fintech/australia"


TO = "batsanuja@gmail.com"             
SUBJECT = "Regarding Job Vacancies of Banks based on Australia"
BODY = "Hello"

keyword="automation"

CAREER_RE=re.compile(r'career|careers|jobs|work\s+with\s+us', re.IGNORECASE)

class vacancy_hunt:
    
    def __init__(self):
        self.browser=Playwright()
        self.tables=Tables()
    
        
    
    def open_browser(self):
        self.browser.new_browser(headless=False,slowMo=10)
        self.browser.new_page(url="about:blank")
        
    
    def search_vacancy_all(self):
        banks=self.tables.read_table_from_csv("output/bank.csv",header=True)
        
        for row in banks:
                name = row["name"]
                try:
                    res = self.search_vacancy(name)
                    # print(name,res)   
                    result = res[name] if res else None
                except Exception as e:
                    print(f"[skip] {row['name']}:{e}")
                    result=None

                if res is None:
                    continue 
                
                save_result(conn, name, result)
        
        # email_text = build_report(conn, new_since=run_started)
        # print(email_text)
        # conn.close()

            
        
    
    def navigate_bank(self):
        self.browser.new_page(url=AUS_BANK)
        elements=self.browser.get_elements("#content > div.inner.animsition > div.main-container > div.left > div.page-content > ul > li > a")
        
        rows=[]
        for e in elements:
            attribute_href=self.browser.get_property(e,"href")
            attribute_name=self.browser.get_property(e,"innerText")
            rows.append({"name":attribute_name,"href":attribute_href })
        table_bank=self.tables.create_table(rows)
        self.tables.write_table_to_csv(table_bank,"output/bank.csv")
    
    def navigate_insurance(self):
        self.browser.new_page(url=AUS_INSURANCE)
        elements=self.browser.get_elements("td>a")
        rows=[]
        for e in elements:
            attribute_href=self.browser.get_property(e,"href")
            attribute_name=self.browser.get_property(e,"innerText")
            rows.append({"name":attribute_name,"href":attribute_href })
            table_insurance=self.tables.create_table(rows)
            self.tables.write_table_to_csv(table_insurance,"output/insurance.csv")
        
        
    def navigate_fintech(self):
        self.browser.new_page(url=AUS_FINTECH)
        
    def close_browser(self):
        self.browser.close_browser()
        
    
    def search_vacancy(self,name):
        
        match name:
            case "AMP Bank":
                career_search="https://fa-esow-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs?keyword=automation&mode=location"
                tile="div.job-tile__header-container > span"
                self.browser.go_to(career_search,timeout="70")
                time.sleep(10)
                elements = self.browser.get_elements(tile)
                titles = [self.browser.get_property(e, "innerText").strip() for e in elements]
                
                # print(titles)        
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                
            
            case "ANZ":
                career_search="https://careers.anz.com/search/?createNewAlert=false&q=automation&locationsearch=australia&optionsFacetsDD_country=&optionsFacetsDD_customfield4=&optionsFacetsDD_customfield5=&optionsFacetsDD_facility=&optionsFacetsDD_customfield1="
                tile="span.jobTitle.hidden-phone"
                self.browser.go_to(career_search,timeout="70")
                time.sleep(10)

                
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                    
                titles=read_titles()
                
                links = self.browser.get_elements("ul.pagination li:not(.active) a[title^='Page']")
                other_pages = []
                for a in links:
                    href = self.browser.get_property(a, "href")
                    if href not in other_pages:
                        other_pages.append(href)
                for url in other_pages:
                    self.browser.go_to(url, timeout="70")
                    time.sleep(10)
                    titles += read_titles()
                  
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                        
                
            case "Commonwealth Bank":
                career_search="https://cba.wd3.myworkdayjobs.com/CommBank_Careers?q=automation&locationCountry=d903bb3fedad45039383f6de334ad4db"
                tile="a.css-19uc56f"
                next_btn = 'button[data-uxi-widget-type="stepToNextButton"]'
                self.browser.go_to(career_search,time_out="70")
                
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                 
                titles = read_titles()                       
                page = 1
                while self.browser.get_element_count(next_btn) > 0:
                    if self.browser.get_property(next_btn, "disabled"):
                        break                                     # last page
                    page += 1
                    self.browser.click(next_btn)
                    # wait until the pagination says we're on the new page
                    self.browser.wait_for_elements_state(
                        f'button[aria-current="page"][aria-label="page {page}"]', "visible", timeout="15s")
                    self.browser.wait_for_elements_state(tile + " >> nth=0", "visible", timeout="15s")
                    titles += read_titles()
                
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                     
            
            case "IMB Bank":
                career_search="https://imbcareers.com.au/job-search-results/?keyword=automation"
                tile="div.jobTitle > a"
                self.browser.go_to(career_search,timeout="70")
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                
                titles = read_titles()
                
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                               
                
                
            case "NAB":
                career_search="https://careers.nab.com.au/jobs/search?page=1&cities%5B%5D=Australia-wide&query=automation" #-> Search for any country automation
                #career_search="https://careers.nab.com.au/jobs/search?page=1&query=a"
                tile="h3.card-title.job-search-results-card-title"
                next_link="ul.pagination li.next:not(.disabled) a.page-link"
                
                self.browser.go_to(career_search,timeout="70")
                time.sleep(5)
        
                titles = []
                seen_urls = set()

                while True:
                    current = self.browser.get_url()
                    if current in seen_urls:                    # safety against loops
                        break
                    seen_urls.add(current)

                    els = self.browser.get_elements(tile)
                    titles += [self.browser.get_property(e, "innerText").strip() for e in els]

                    if self.browser.get_element_count(next_link) == 0:
                        break                                   # last page: next is disabled
                    href = self.browser.get_property(next_link + " >> nth=0", "href")
                    self.browser.go_to(href, timeout="70")
                            
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                            
                        
                
            case "St George Bank" | "Westpac" | "Bank of Melbourne" | "BankSA"| "": #westpac-index out of range
                career_search="https://ebuu.fa.ap1.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/jobs?keyword=automation&location=Australia&locationId=300000000294772&locationLevel=country&mode=location"
                button_element="button.button.text-color-primary.font-family-secondary"
                tile="span.job-tile__title"
                self.browser.go_to(career_search,timeout="70")
                time.sleep(5)
                
                while True:
                    if self.browser.get_element_count(button_element) > 0:
                        self.browser.scroll_to_element(button_element)
                        self.browser.click(button_element)
                        time.sleep(5)
                    else:
                        break
                    
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                                                    
                titles = read_titles()
                                
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                            
                
            case "Suncorp Group":
                career_search="https://fa-evew-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs?keyword=automation&location=Australia&locationId=300000000473001&locationLevel=country&mode=job-location"
                tile="div.job-tile__header-container"
                self.browser.go_to(career_search,timeout="70")
                time.sleep(7)
                self.browser.scroll_to_element("footer.app-footer")
                
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                                                                    
                titles = read_titles()
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                 
                
            
            case "Beyond Bank Australia": 
                career_search="https://www.beyondbank.com.au/careers/current-opportunities/"
                tile="td.srJobListJobTitle"
                self.browser.go_to(career_search,timeout="70")
                time.sleep(3)
                def read_titles():
                    els = self.browser.get_elements(tile)
                    titles = [self.browser.get_property(e, "innerText").strip() for e in els]
                    return [t for t in titles if keyword.lower() in t.lower()]
                
                titles = read_titles()
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                  
            
            # case "Defence Bank": #couldn't detect input locator -> Captcha
            #     career_search="https://www.defencebank.com.au/about-us/careers/job-listings/" #-> Need to search manually
            #     tile="a.e-clickable.redirect_elmo_link"
            #     input_xpath="xpath=/html/body/div/div[1]/div/div[1]/div/div/form/div[1]/div/div/div/input"
            #     input="div.input-group > input#search-text.form-control"
            #     self.browser.go_to(career_search,timeout="30")
            #     # self.browser.switch_page("NEW")
            #     time.sleep(5)
                
            #     # self.browser.switch_page("NEW")
            #     # self.browser.fill_text(input_xpath,keyword)
            #     # self.browser.fill_text("#search-text", "automation")
                
            #     element = self.browser.find_element("#search-text")

            #     print("Visible:", element.is_visible())
            #     print("Enabled:", element.is_enabled())
                
            #     self.browser.keyboard_key("press","Enter")
            #     def read_titles():
            #         els = self.browser.get_elements(tile)
            #         return [self.browser.get_property(e, "innerText").strip() for e in els]        
                
            #     titles = read_titles()
            #     return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                         
                
                
            # case "Bendigo Bank": 
            #     career_search="https://careers.bendigobank.com.au/search/?q=manager&locationsearch=&searchResultView=LIST&pageNumber=0&facetFilters=%7B%7D&sortBy=&markerViewed=&carouselIndex="
            #     tile="a.jobCardTitle.JobsList_jobCardTitle__pRNjw"
            #     next_btn="button#goToNextPageBtn"
            #     self.browser.go_to(career_search,timeout="40")
            #     time.sleep(8)
                
            #     def read_titles():
            #         els = self.browser.get_elements(tile)
            #         titles = [self.browser.get_property(e, "innerText").strip() for e in els]
            #         return titles
                
            #     titles = read_titles()
                   
            #     while True:
            #         if self.browser.get_element_count(next_btn) > 0:
            #             self.browser.click(next_btn)
            #             time.sleep(4)
            #             titles+=read_titles()
            #         else: break
                
                
            #     return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                 
                
                
                
            case "Hume Bank": #Not tested for next page due to unavailability
                career_search="https://www.humebank.com.au/why-hume-bank/careers-at-hume-bank/"
                self.browser.go_to(career_search,timeout="70")
                tile="div.job > h2.title"
                def read_titles():
                    els = self.browser.get_elements(tile)
                    titles = [self.browser.get_property(e, "innerText").strip() for e in els]
                    return [
                        t for t in titles
                        if t != "[VACANCY_NAME]" and keyword.lower() in t.lower()
                    ]
                                                                    
                titles = read_titles()
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                
                
                
            # case "Teachers Mutual Bank": #not tested
            #     career_search="https://www.linkedin.com/jobs/teachers-mutual-bank-limited-jobs-worldwide?f_C=285023&trk=job-results_see-all-jobs-link&original_referer=https%3A%2F%2Fwww.linkedin.com%2Fcompany%2Ftmbl%2Fjobs%2F&position=1&pageNum=0"
            #     return
            
            case "Bank of Sydney":
                career_search="https://www.datakiosk.com.au/cirrus/usercontrols/journey/careers_joblist.aspx?kiosk=67251297A73D91045FC3893A366D345B&MD5=64938968784E33F6D6C1B665D6DF21A0&SecureID=C17B2CD6A8412025ED5EA1817E12CF1D"
                tile=" div.inner-grid > a >h6"
                
                self.browser.go_to(career_search,timeout="70")
                self.browser.fill_text("input.form-control.my-3",keyword)
                self.browser.keyboard_key("press","Enter")
                def read_titles():
                    els = self.browser.get_elements(tile)
                    titles = [self.browser.get_property(e, "innerText").strip() for e in els]
                    return [t for t in titles if t!="[VACANCY_NAME]"]
                                                
                titles = read_titles()
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                
            
            
            # case "Bank Australia": 
            #     career_search="https://www.bankaust.com.au/page/search-bank-australia-jobs"#-> can't search directly
            #     search_element="input#search-text"
            #     tile="li.list-group-item > div.row > div > p >a"
            #     self.browser.go_to(career_search,timeout="30")
            #     self.browser.fill_text(search_element,"automaiton")
            #     self.browser.keyboard_key("press","Enter")
                
            #     return
            
            case "Macquarie Bank":
                career_search="https://recruitment.macquarie.com/en_US/careers/SearchJobs/automation?10671=%5B871429%5D&10671_format=21337&listFilterMode=1&jobRecordsPerPage=9&"
                tile="div.article__header"
                next_element="a.paginationNextLink"
                self.browser.go_to(career_search ,timeout="70")
                # time.sleep(10)
                
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                 
                titles=read_titles() 
                
                self.browser.click("a.cookiesButtonSave")
                
                next=self.browser.get_element(next_element)   
                   
                while True:
                    if self.browser.get_element_count(next_element):
                        self.browser.click(next_element)
                        time.sleep(3)
                        titles+=read_titles()
                    else: break
                                    
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
            
            case "BankVic":        
                career_search="https://clientapps.jobadder.com/90145/bankvic-careers?keyword=automation"
                #career_search="https://clientapps.jobadder.com/90145/bankvic-careers"
                tile="a.viewjob"
                self.browser.go_to(career_search,timeout="70")
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                                 
                titles = read_titles()
                
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
            
           
            
            case "Bank of Queensland":
                career_search="https://boq.wd3.myworkdayjobs.com/en-GB/Careers-at-BOQGroup?q=automation"
                #career_search="https://boq.wd3.myworkdayjobs.com/en-GB/Careers-at-BOQGroup"
                self.browser.go_to(career_search)
                tile="a.css-19uc56f"
                next_btn = 'button[data-uxi-widget-type="stepToNextButton"]'
                self.browser.go_to(career_search,timeout="70")
                                
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                                 
                titles = read_titles()                       
                page = 1
                while self.browser.get_element_count(next_btn) > 0:
                    if self.browser.get_property(next_btn, "disabled"):
                        break                                     # last page
                    page += 1
                    self.browser.click(next_btn)
                    # wait until the pagination says we're on the new page
                    self.browser.wait_for_elements_state(
                    f'button[aria-current="page"][aria-label="page {page}"]', "visible", timeout="15s")
                    self.browser.wait_for_elements_state(tile + " >> nth=0", "visible", timeout="15s")
                    titles += read_titles()
                                
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                
            
            case "Heritage Bank":
                career_search="https://hcyt.fa.ap1.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/jobs?keyword=automation&lastSelectedFacet=LOCATIONS&mode=location&selectedLocationsFacet=300000000361214"
                #career_search="https://hcyt.fa.ap1.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/jobs?lastSelectedFacet=LOCATIONS&mode=location&selectedLocationsFacet=300000000361214"
                last_element="footer.app-footer"
                tile="div.job-tile__header-container"
                
                self.browser.go_to(career_search,timeout="70")
                time.sleep(6)

                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                
                self.browser.scroll_to_element(last_element)
                titles=read_titles()
                
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                
            
            
            case "Bankwest":
                career_search="https://cba.wd3.myworkdayjobs.com/Bankwest_Careers?q=automation" 
                #career_search="https://cba.wd3.myworkdayjobs.com/Bankwest_Careers"
                tile="a.css-19uc56f"
                next_btn = 'button[data-uxi-widget-type="stepToNextButton"]'
                self.browser.go_to(career_search,timeout="70")
                                
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                                 
                titles = read_titles()                       
                page = 1
                while self.browser.get_element_count(next_btn) > 0:
                    if self.browser.get_property(next_btn, "disabled"):
                        break                                     # last page
                    page += 1
                    self.browser.click(next_btn)
                    # wait until the pagination says we're on the new page
                    self.browser.wait_for_elements_state(
                    f'button[aria-current="page"][aria-label="page {page}"]', "visible", timeout="15s")
                    self.browser.wait_for_elements_state(tile + " >> nth=0", "visible", timeout="15s")
                    titles += read_titles()
                                
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                
            
            case "P&N Bank":
                career_search="https://www.pnbank.com.au/careers/find-your-dream-job/" #=> Not specified\
                tile="div.job>h2.title"
                self.browser.go_to(career_search)
                print(self.browser.get_elements(tile))
                # titles=[]
                
                def read_titles():
                    els = self.browser.get_elements(tile)
                    titles=[self.browser.get_property(e, "innerText").strip() for e in els]
                    return [t for t in titles if keyword.lower() in t.lower()]
                titles=read_titles()                                
                
                
                  
                
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
            
            # case "MyState Bank": #Captcha
            #     #career_search=""
            #     return
            
            case "HIFX": #2nd page cloudflare human identification
                #career_search="https://careers.xe.com/search/jobs?q=automation&location=australia"
                career_search="https://careers.xe.com/search/jobs/in?location=&page=1&q=#"
                tile="div.jobs-section__item.padded-v-small > div > div >h2"
                next_element="a.next_page"
                
                self.browser.go_to(career_search,timeout="70")
                
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]
                                
                titles=read_titles()
                
                # while True:
                #     if self.browser.get_element_count(next_element):
                #         self.browser.click(next_element)
                #         titles+=read_titles()
                #     else: break
                                
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}

                
                
                
            
            # case "ING Direct": # input can't be checked -> Error
            #     career_search="https://careers.ing.com/en/search-jobs?k=automation&l=&orgIds=2618"
            #     #aus_check='input#country-filter-0[data-id="2077456"]'
            #     tile="h2.search-results-item__title.vacancy-item__title"
            #     cookie_button="button#igdpr-reject-button"
                
            #     self.browser.go_to(career_search)
            #     self.browser.click(cookie_button)
            #     self.browser.click("button#country-toggle")
            #     aus_check = "//input[@id='country-filter-0']"
            #     sp_check="//input[@id='country-filter-11']"
            #     aus_label = "//label[@for='country-filter-0']"
            #     sp_label="//label[@for='country-filter-11']"

                                
            #     self.browser.wait_for_elements_state(
            #         "(//ul[@class='search-filter-list '])[1]",
            #         "visible",
            #         timeout="15s"
            #     )

            #     self.browser.scroll_to_element(aus_label)

            #     # Check current checkbox state
            #     is_checked = self.browser.get_element_states(aus_check)
            #     print(is_checked)

            #     if "checked" not in is_checked:
            #         self.browser.click(aus_label)
                    
            #     is_checked=self.browser.get_element_states(sp_check)    
                
            #     # if "checked" not in is_checked:
            #     #     self.browser.click(sp_label)
                
            #     self.browser.click(aus_label)

            #     def read_titles():
            #         els = self.browser.get_elements(tile)
            #         return [self.browser.get_property(e, "innerText").strip() for e in els]
                
            #     titles=read_titles()
                
            #     return {name: {"count": len(titles), "url": career_search, "titles": titles}}
            
            
            # case "Citigroup":
            #     career_search="https://jobs.citi.com/search-jobs?k=automation&l=&orgIds=287"    
            #     input_check='ul.search-filter-list > li >input.filter-checkbox[data-display="Australia"]'
            #     button_region="button#country-toggle"
            #     tile="a.sr-job-item__link"
            #     next_element="a.next"
                
                
            #     self.browser.go_to(career_search)
            #     self.browser.click("button#system-ialert-reject-button")
                
                
            #     self.browser.click(button_region)
            #     self.browser.check_checkbox(input_check)
                
            #     time.sleep(6)
                
            #     def read_titles():
            #         els = self.browser.get_elements(tile)
            #         return [self.browser.get_property(e, "innerText").strip() for e in els]
                
            #     titles=read_titles()
                
            #     while True:
            #         cls=self.browser.get_attribute(next_element,"class") or ""
            #         if "disabled" in cls:
            #             break
            #         else:    
            #             self.browser.click(next_element)
            #             titles+=read_titles()
                    
                    
            #     return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                   
                
                
            
            
            # case "Deutsche Bank Australia": #Load element can't clicked -> Error
            #     #career_search="https://careers.db.com/professionals/search-roles/#/professional/results/?searchType=profession&country=17" #-> Can't search directly with keyword
            #     career_search="https://careers.db.com/professionals/search-roles/#/professional/results/?searchType=profession"
            #     input_element="input#jobIdSearch"
            #     load_element="button.button.type-primary >> nth=2"
            #     #load_more="xpath=/html/body/div[1]/section[4]/div/div/div/section/div/div/div/div/div/div[2]/div/div[22]/button"
            #     tile="div.detail-entry >h2"
            #     self.browser.go_to(career_search)
                
            #     self.browser.click("button[data-testid='uc-deny-all-button']")
                
            #     self.browser.fill_text(input_element,"manager")
            #     time.sleep(6)
            #     self.browser.click("xpath=/html/body/div[1]/section[4]/div/div/div/section/div/div/div/div/div/div[1]/div/div[3]/button")
            #     #self.browser.click("button.button.type-primary")
                
            #     def read_titles():
            #         els = self.browser.get_elements(tile)
            #         return [self.browser.get_property(e, "innerText").strip() for e in els]        
                                     
                
            #     while True:
            #         if (self.browser.get_element_count(load_element)) == 0:
            #             titles=read_titles()
            #             break
                    
            #         self.browser.scroll_to_element(load_element)
            #         self.browser.click(load_element)
                
            #     return {name: {"count": len(titles), "url": career_search, "titles": titles}}
                                                                    
                
            
            case "Rabobank":
                career_search="https://rabobank.jobs/en/jobs/?country=au&job_type[]=professionals&location%5Bcountry%5D=au&q=automation"  
                #career_search="https://rabobank.jobs/en/jobs/?job_type[]=professionals&location%5Bcountry%5D=au&page=1&q=manager"
                next_btn='button[aria-label="Next page"]'
                tile="a.src_features_buildingBlocks_Card_componentCardLink.src_features_buildingBlocks_Card_linkLayout"
                self.browser.go_to(career_search,timeout="70")
                time.sleep(5)
                
                def read_titles():
                    els = self.browser.get_elements(tile)
                    return [self.browser.get_property(e, "innerText").strip() for e in els]        
                                
                titles = read_titles()
                
                while True:
                    
                    if self.browser.get_element_count(next_btn) == 0:
                        break
                    
                    cls = self.browser.get_attribute(next_btn, "class") or ""
                    if "disabled" in cls:
                        break                                    # last page already read, so stop

                    self.browser.click(next_btn) 
                    titles += read_titles()
                            
                return {name: {"count": len(titles), "url": career_search, "titles": titles}}
            
            case default:
                return None
    
        
        
        
@task
def entrance():
    
    vacancy=vacancy_hunt()
    try:
        vacancy.open_browser()
        # vacancy.navigate_bank()
        # vacancy.search_vacancy_all()
        # vacancy.navigate_insurance()
        # vacancy.navigate_fintech()
        vacancy.search_vacancy("AMP Bank")
    
    except Exception as e:
        print(e)    
    
    finally:
        vacancy.close_browser()
        
        
@task
def create_email():
    get_credentials()
    send_email(TO, SUBJECT,  build_report(conn, new_since=run_started))      
        
            
        
    
    
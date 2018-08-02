# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# This script serves to do data cleaning
from bs4 import BeautifulSoup
import logging
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
import os.path
import pandas as pd
import re
import sys

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# English Stopwords
with open('stopwords.txt') as file:
    stopwords = file.read().split()
file.close()


class SentenceParser:

    regex_str = [
        r'<[^>]+>',                                                                     # HTML tags
        r'(?:@[\w_]+)',                                                                 # @-mentions
        r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)",                                               # hash-tags
        r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+',   # URLs
        r'(?:(?:\d+,?)+(?:\.?\d+)?)',                                                   # numbers
        r"(?:[a-z][a-z'\-_]+[a-z])",                                                    # words with - and '
        r'(?:[\w_]+)',                                                                  # other words
        r'(?:\S)'                                                                       # anything else
    ]

    def __init__(self, loggingLevel = 20):
        self.data = None
        # extract words stem
        self.porter = nltk.PorterStemmer()
        # a set of stopwords
        self.stops = set(stopwords)
        logging.basicConfig(level=loggingLevel)
        pass

    # pandas read csv/json/xlsx files to dataframe format
    def read_file(self, filepath, filetype, encod='ISO-8859-1', header=None):
        LOGGER.info('Start reading File')
        if not os.path.isfile(filepath):
            LOGGER.error("File Not Exist!")
            sys.exit()
        if filetype == 'csv':
            df = pd.read_csv(filepath, encoding=encod, header=header)
        elif filetype == 'json':
            df = pd.read_json(filepath, encoding=encod, lines=False)
        elif filetype == 'xlsx':
            df = pd.read_excel(filepath, encoding=encod, header=header)
        else:
            LOGGER.error("Extension Type not Accepted!")
            sys.exit()

        LOGGER.debug(df)
        self.data = df

    # Operation on the DataFrame
    def merge_column(self, columns, name):
        LOGGER.info('Merge headers %s to %s', str(columns), name)
        self.data[name] = ''
        for header in columns:
            self.data[name] += ' ' + self.data[header]
  
    # Remove template
    def clean_body(self, column, remove_template=True, remove_code=True):
        # clean issue's description from template
        LOGGER.info("Start Removing Templates..")
        for i in range(len(self.data)):
            # remove 'Environment info' part
            if remove_template and "## Environment info" in self.data[column][i]:
                index = self.data.loc[i, column].find("## Environment info")
                self.data.loc[i, column] = self.data.loc[i, column][:index]
            # remove code
            if remove_code and "```" in self.data[column][i]:
                sample = self.data[column][i].split("```")
                sample = [sample[i*2] for i in range(0, int((len(sample)+1)/2))]
                self.data.loc[i,column] = " ".join(sample)

    # Start cleaning the text from column
    def process_text(self, column, remove_symbol=True, remove_stopwords=False, stemming=False):
        LOGGER.info("Start Data Cleaning...")
        # remove some symbols
        self.data[column] = self.data[column].str.replace(r'[\n\r\t]+', ' ')
        # remove URLs
        self.data[column] = self.data[column].str.replace(self.regex_str[3], ' ')
        tempcol = self.data[column].values.tolist()

        for i in range(len(tempcol)):
            row = BeautifulSoup(tempcol[i], 'html.parser').get_text().lower()
            # remove symbols
            if remove_symbol:
                row = re.sub('[^a-zA-Z]', ' ', row)
            words = row.split()
            # remove stopwords
            if remove_stopwords:
                words = [w for w in words if w not in self.stops and not w.replace('.', '', 1).isdigit()]
            # extract words stem
            if stemming:
                words = [self.porter.stem(w) for w in words] 
            row = ' '.join(words)
            tempcol[i] = row.lower()
        return tempcol

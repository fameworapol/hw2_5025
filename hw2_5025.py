#!/usr/bin/env python
# coding: utf-8

# In[3]:


import boto3
import botocore
import pandas as pd
from IPython.display import display, Markdown
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')


# In[4]:


def create_bucket(bucket):
    import logging

    try:
        s3.create_bucket(Bucket=bucket)
    except botocore.exceptions.ClientError as e:
        logging.error(e)
        return 'Bucket ' + bucket + ' could not be created.'
    return 'Created or already exists ' + bucket + ' bucket.'
create_bucket('nyctlc-cs653-5025')


# In[5]:


def list_buckets(match=''):
    response = s3.list_buckets()
    if match:
        print(f'Existing buckets containing "{match}" string:')
    else:
        print('All existing buckets:')
    for bucket in response['Buckets']:
        if match:
            if match in bucket["Name"]:
                print(f'  {bucket["Name"]}')

list_buckets(match='open')


# In[6]:


def list_bucket_contents(bucket, match='', size_mb=0):
    bucket_resource = s3_resource.Bucket(bucket)
    total_size_gb = 0
    total_files = 0
    match_size_gb = 0
    match_files = 0
    for key in bucket_resource.objects.all():
        key_size_mb = key.size/1024/1024
        total_size_gb += key_size_mb
        total_files += 1
        list_check = False
        if not match:
            list_check = True
        elif match in key.key:
            list_check = True
        if list_check and not size_mb:
            match_files += 1
            match_size_gb += key_size_mb
            print(f'{key.key} ({key_size_mb:3.0f}MB)')
        elif list_check and key_size_mb <= size_mb:
            match_files += 1
            match_size_gb += key_size_mb
            print(f'{key.key} ({key_size_mb:3.0f}MB)')

    if match:
        print(f'Matched file size is {match_size_gb/1024:3.1f}GB with {match_files} files')            
    
    print(f'Bucket {bucket} total size is {total_size_gb/1024:3.1f}GB with {total_files} files')
list_bucket_contents(bucket='nyc-tlc', match='2017', size_mb=250)


# In[7]:


pip install pyarrow


# In[8]:


def preview_csv_dataset(bucket, key, rows=10):
    data_source = {
            'Bucket': bucket,
            'Key': key
        }
    # Generate the URL to get Key from Bucket
    url = s3.generate_presigned_url(
        ClientMethod = 'get_object',
        Params = data_source
    )

    data = pd.read_parquet(url,'pyarrow')
    return data
df = preview_csv_dataset(bucket='nyc-tlc', key='trip data/yellow_tripdata_2017-01.parquet', rows=100)
df.head()


# In[9]:


def key_exists(bucket, key):
    try:
        s3_resource.Object(bucket, key).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # The key does not exist.
            return(False)
        else:
            # Something else has gone wrong.
            raise
    else:
        # The key does exist.
        return(True)

def copy_among_buckets(from_bucket, from_key, to_bucket, to_key):
    if not key_exists(to_bucket, to_key):
        s3_resource.meta.client.copy({'Bucket': from_bucket, 'Key': from_key}, 
                                        to_bucket, to_key)        
        print(f'File {to_key} saved to S3 bucket {to_bucket}')
    else:
        print(f'File {to_key} already exists in S3 bucket {to_bucket}')


# In[10]:


for i in range(1,6):
    copy_among_buckets(from_bucket='nyc-tlc', from_key=f'trip data/yellow_tripdata_2017-0{i}.parquet',
                      to_bucket='nyctlc-cs653-5025', to_key=f'yellow_tripdata_2017-{i}.parquet')


# In[11]:


'''
a.) 
'''


# In[12]:


sum = 0
for i in range(1,6):
    resp = s3.select_object_content(
    Bucket='nyctlc-cs653-5025',
    Key='yellow_tripdata_2017-1.parquet',
    ExpressionType='SQL',
    Expression=f"SELECT COUNT(payment_type) FROM s3object s WHERE payment_type={i}",
    InputSerialization = {'Parquet':{}},
    OutputSerialization = {'CSV': {}},
    )

    for event in resp['Payload']:
        if 'Records' in event:
            records = event['Records']['Payload'].decode('utf-8') 
            sum = sum + int(records)
            print(f"จำนวน yellow taxi ที่มี paymeent_type = {i} คือ {records}")
print(f"มี yellow taxi ทั้งหมดเป็น {sum} คัน")


# In[13]:


'''
b.)
'''


# In[14]:


import numpy as np
yellow_jan_PULocationID = df['PULocationID'].unique()
np.sort(yellow_jan_PULocationID)


# In[24]:


for i in range(1,266):
    s3_select_results_countloc = s3.select_object_content(
        Bucket='nyctlc-cs653-5025',
        Key='yellow_tripdata_2017-1.parquet',
        Expression="SELECT count(PULocationID) FROM s3object s WHERE PULocationID = {}".format(i),
        ExpressionType='SQL',
        InputSerialization={'Parquet': {}},
        OutputSerialization={'CSV': {}},
    )
    s3_select_results_sumfare = s3.select_object_content(
        Bucket='nyctlc-cs653-5025',
        Key='yellow_tripdata_2017-1.parquet',
        Expression="SELECT sum(fare_amount) FROM s3object s WHERE PULocationID = {}".format(i),
        ExpressionType='SQL',
        InputSerialization={'Parquet': {}},
        OutputSerialization={'CSV': {}},
    )
    s3_select_results_avgpass = s3.select_object_content(
        Bucket='nyctlc-cs653-5025',
        Key='yellow_tripdata_2017-1.parquet',
        Expression="SELECT avg(passenger_count) FROM s3object s WHERE PULocationID = {}".format(i),
        ExpressionType='SQL',
        InputSerialization={'Parquet': {}},
        OutputSerialization={'CSV': {}},
    )
    for event in s3_select_results_countloc['Payload']:
        if 'Records' in event:
            records = event['Records']['Payload'].decode('utf-8')
            records = int(records)
    print("No. of rides in Location {} = {}".format(i, records))
    for event in s3_select_results_sumfare['Payload']:
        if 'Records' in event:
            records = event['Records']['Payload'].decode('utf-8')
            records = float(records)
    print("Sum fare amount in Location {} = {:.2f}".format(i, records))
    for event in s3_select_results_avgpass['Payload']:
        if 'Records' in event:
            records = event['Records']['Payload'].decode('utf-8')
            records = float(records)
    print("Average no. of passenger in Location {} = {:.2f}".format(i, records))


# In[53]:


for month in range(1,4):
    print("2017, Month: {}".format(month))
    for type in range(1,6):
        s3_select_results_3m = s3.select_object_content(
            Bucket='nyctlc-cs653-5025',
            Key="yellow_tripdata_2017-{}.parquet".format(month),
            Expression="SELECT count(payment_type) FROM s3object s WHERE payment_type = {}".format(type),
            ExpressionType='SQL',
            InputSerialization={'Parquet': {}},
            OutputSerialization={'CSV': {}},
        )
        for event in s3_select_results_3m['Payload']:
            if 'Records' in event:
                records = event['Records']['Payload'].decode('utf-8')
                records = float(records)
        print("No. of payment_type {} = {}".format(type, records))
    print("---")


# In[ ]:





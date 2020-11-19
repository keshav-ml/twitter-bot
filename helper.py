import pandas as pd
import numpy as np

def GetDM(api):
  dms = api.list_direct_messages(500)
  msg = []
  sender_id = []
  reciever_id = []
  timestamp = []
  for dm in dms:
    timestamp.append(dm._json['created_timestamp'])
    sender_id.append(dm._json['message_create']['sender_id'])
    reciever_id.append(dm._json['message_create']['target']['recipient_id'])
    msg.append(dm._json['message_create']['message_data']['text'])
  data_df = pd.DataFrame({"timestamp":timestamp,"sender_id":sender_id,"reciever_id":reciever_id,"text":msg},columns=['timestamp','sender_id','reciever_id','text'])
  data_df['timestamp'] = data_df['timestamp'].astype(float)
  data_df.sort_values("timestamp",ascending=False,inplace=True)

  uid = api.me().id_str

  s_data = [api.get_user(sid)._json for sid in data_df[data_df['sender_id'] != uid]['sender_id']]
  s_data = list({s['id_str']:s for s in s_data}.values())


  return data_df,s_data
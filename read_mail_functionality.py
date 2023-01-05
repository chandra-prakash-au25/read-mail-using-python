import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
BASE_DIR = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+"/rto_dashboard/"     
BASE_DIR1 = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))+"/rto_dashboard/rt0_files/"     

@csrf_exempt
def viewreplyemail(request):
    obj = json.loads(request.body.decode('utf-8'))
    print(obj)
    query='from:cp150496@gmail.com is:unread subject:Re:kuch krlo'
    res=Read_emails(query)
    result=''
    for mails in res:
        result_mails=mails
    cust_email = obj['email']
    # sub_name = ('Re:'+'READ Emails Using python').replace(" ", "")
    sub_name = ('Re:'+'Order '+obj['order_id']+': Returned - Response Required').replace(" ", "")
    _file_path = obj['file_path']
    workorder_id = obj['workorder_id']
    try:
        reply_email_data =  read_rto_replied_mail(workorder_id,cust_email,sub_name,_file_path,result_mails)
    except Exception as e:
        print(e)
        return JsonResponse({"status":str(e),"data":[],'file_path_str':""}, safe=False)

    return JsonResponse({"status":"true","data":reply_email_data['replied_email_data_array'],'file_path_str':reply_email_data['file_path_str']}, safe=False)

def read_rto_replied_mail(workorder_id,cust_email,pre_sub_name,_file_path,mail_data):
    replied_email_data_array=[]
    response_data={}           
    print(mail_data)
    sender_data=mail_data[0][0]
    mails_data=mail_data[1]
    print('========================================= bug')
    if len(mails_data)==2:
        response_data['files'] = mails_data[1]
    txt=mails_data[0]['data']
    message = txt.split('wrote:')
    no_of_mess=(len(message))
    index=no_of_mess-2
    print(index,'======',(message[index]))
    if "crn" in message[index] or "CrN" in message[index] or 'CRN' in message[index]:
        print("you order cancelled")
    response_data['subject'] = sender_data['subject']
    response_data['to'] =sender_data['to']
    response_data['from'] = sender_data['from']
    response_data['date'] = sender_data['date']
    response_data['message'] =mails_data[0]['data']
    replied_email_data_array.append(response_data)
    return {'replied_email_data_array':replied_email_data_array,'file_path_str':'_file_path_str'}

# this functionality for file upload to s3 cloud so i have commented  for now
                    # response_data['message'] = (((str(text1).replace("\\r", "")).replace("\\n", "")).replace("b'", "")).replace("'\xc2\xa0'", "")
                    
                #if part.get_content_maintype() == 'multipart':
                #    continue
                #if part.get('Content-Disposition') is None:
                #    continue
                #fileName = part.get_filename()
                #if bool(fileName):
                #    try:
                #        if (_file_path == None) or (_file_path == ''):
                #            ctime=datetime.now(timezone("Asia/Kolkata")).strftime("%H:%M:%S")
                #            _obj_name = cust_email+'_'+pre_sub_name+'_'+ctime+'.'+str(fileName.split(".")[-1])
                #            LambdaFunctions.upload_object_to_s3(io.BytesIO(part.get_payload(decode=True)),'btc-shipping-option-tracking',_obj_name)
                #            s3_shippingoptiontracking_url ='https://btc-shipping-option-tracking.s3.ap-south-1.amazonaws.com/'+_obj_name
                #            print("URL::"+s3_shippingoptiontracking_url)
                #            if _file_path_str == '':
                #                _file_path_str = _file_path_str + s3_shippingoptiontracking_url
                #            else:
                #                _file_path_str = _file_path_str +','+ s3_shippingoptiontracking_url
                #    except Exception as e:
                #        print(e)
    #print("_file_path_str====")
    #print(_file_path_str)
    #if _file_path_str != '':
    #    print("IF====")
    #    rto_obj = rtocustomerorders.objects.filter(workorder_id=workorder_id)
    #    rto_obj.update(file_path=_file_path_str)
    #replied_email_data_array.append(response_data)
    #if(len(response_data)==0):
    #    replied_email_data_array = []

    #return {'replied_email_data_array':replied_email_data_array,'file_path_str':'_file_path_str'}
def gmail_authenticate():
    creds = None
    creds = Credentials.from_authorized_user_file(BASE_DIR+'token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                BASE_DIR+'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

service = gmail_authenticate()


def Read_emails(query):
    details_reply=[]
    results = search_messages(service, query)
    for msg in results:
        details=read_message(service, msg)
        details_reply.append(details)
        break
    print(details_reply)
    return details_reply


def search_messages(service, query):
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me', pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages



def read_message(service, message):
    msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
    payload = msg['payload']
    headers = payload.get("headers")
    parts = payload.get("parts")
    folder_name = "email"
    has_subject = False
    data={}
    details_data=[]
    if headers:
        for header in headers:
            name = header.get("name")
            value = header.get("value")
            if name.lower() == 'from':
                # we print the From address
                print("From:", value)
                data['from']=value

            if name.lower() == "to":
                # we print the To address
                print("To:", value)
                data['to']=value


            if name.lower() == "subject":
                print("Subject:", value)
                data['subject']=value

            if name.lower() == "date":
                print("Date:", value)
                data['date']=value
    link_data=[]
    data_list=parse_parts(service, parts, "rto_files", message,link_data)
    print(data_list,'===========')
    details_data.append([data])
    details_data.append(data_list)
    print("="*50)
    return details_data



def parse_parts(service, parts, folder_name, message,link_data):
    data_list1=[]
    if parts:
        counter=0
        data_list={}
        data_list={}
        data_list2={}
        for part in parts:
            filename = part.get("filename")
            mimeType = part.get("mimeType")
            body = part.get("body")
            data = body.get("data")
            file_size = body.get("size")
            part_headers = part.get("headers")
            if part.get("parts"):
                data_list1=parse_parts(service, part.get("parts"), folder_name, message,link_data)
            if mimeType == "text/plain":
                print("-______________________")
                if data:
                    text = urlsafe_b64decode(data).decode()
                    if text:
                        data_list2['data']=text
                        data_list1.append(data_list2)

            else:
                counter=0
                data_list={}
                for part_header in part_headers:
                    part_header_name = part_header.get("name")
                    part_header_value = part_header.get("value")
                    if part_header_name == "Content-Disposition":
                        if "attachment" in part_header_value:
                            print("Saving the file:", filename, "size:", get_size_format(file_size))
                            attachment_id = body.get("attachmentId")
                            attachment = service.users().messages() \
                                        .attachments().get(id=attachment_id, userId='me', messageId=message['id']).execute()
                            data = attachment.get("data")
                            data=file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                            filepath = os.path.join(folder_name, filename)
                            index="link"+'_'+str(counter)
                            data_list[index]=(filepath)
                            link_data.append(data_list)
                            data_list1.append(link_data)
                            if data:
                                with open(filepath, "wb") as f:
                                    f.write(data)
   
    return data_list1



def get_size_format(b, factor=1024, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


def clean(text):
    return "".join(c if c.isalnum() else "_" for c in text)













#here code for cancelation of the oreder
def cancel_order_on_email(data):
    pass
    #work_id=data['workorder_id']
    #emails = []
    #postshipmaillogs_array = []
    #customer_order_obj = CustomerOrder.objects.filter(workorder_id=work_id,hasSubscription=False).prefetch_related('items', 'address', 'batchid', 'items__products','shipping_option')
    #rto_order_cancelled = 'rto_order_cancelled'
    #for cust_order in customer_order_obj:
    #    cust_email = cust_order.Email
    #    order_id = cust_order.order_id
    #    cust_name = cust_order.customer_name
    #    total_amount = cust_order.total_amount
    #    last_courier_scan = ''
    #    if cust_email:
    #        for shipingoption in cust_order.shipping_option.all():
    #            if shipingoption.delivery_status:
    #                last_courier_scan = shipingoption.details
#
    #        items_array=[]
    #        for line_item in cust_order.items.all():
    #            items_array.append({"item":line_item.product_id,"restock":True})
    #    
    #    t=gettemplate(rto_order_cancelled)
    #    t=t.replace('{{customer_name}}',cust_name)
    #    t=t.replace('{{last_courier_scan}}',last_courier_scan)
    #    subject_name = "Order "+order_id+": Cancelled"
    #    emails.append(mass_mail_obj(subject_name,t,[cust_email]))
    #    postshipmaillogs_array.append({"batchid":cust_order.batchid.pk,"workorder_id":cust_order.workorder_id,"template_name":rto_order_cancelled,"template_body":t,'items':items_array,'total_amount':total_amount})
#
    #if len(emails) > 0:
    #    print("SENDING MAIL:::::::::::")
    #    get_connection().send_messages(emails)
    #    created_on=datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    #    for obj in postshipmaillogs_array:
    #        rto_obj = rtocustomerorders.objects.filter(workorder_id=obj['workorder_id'])
    #        rto_obj.update(cancel_mail_template=rto_order_cancelled,mail_status='canceled')
    #        transitdelaymaillogs_obj = postshipmaillogs.objects.create(batchid=obj['batchid'],workorder_id=obj['workorder_id'],template_name=rto_order_cancelled,template_body=obj['template_body'],created_on=created_on,created_by='dash',status='sent')
    #        transitdelaymaillogs_obj.save()
#
    #    try:
    #        cancel_rto_orders_func(postshipmaillogs_array)
    #    except Exception as e:
    #        print(e)
#
    #    print("SENT MAIL:::::::::::")






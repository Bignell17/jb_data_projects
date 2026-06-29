%run /Workspace/Shared/BI/pipelines/adhoc/email_api/automated_email_sending

# COMMAND ----------


# Get the current date
from datetime import datetime
current_date = datetime.now()


# Get the previous month's full name (e.g., "March")
month_name = current_date.strftime('%B')
print(month_name)


# COMMAND ----------


message = f"""
Hi Fiona and Neil,
<br><br>
Please find the latest AQ Report for <b>{month_name} 2025</b>.
<br><br>
For any queries, please reach out to Rachel Fisken. 
<br><br>
Kind regards,
<br><br>
Data Analytics Team
"""
display(HTML(message))


# COMMAND ----------


send_email_with_attachments(
    access_token=access_token,
    from_email='DataAnalytics@80hg.io',
    to_email=['Email_1@Address.com', 'Email_2@Address.com', 'Email_3@Address.com'],
    email_subject='AQ Report',
    content_type="HTML",
    content_body=message,
    dfs=[None],
    attachment_names=[None],
    file_paths=[excel_path_combined],
    attachment_format='xlsx'
)

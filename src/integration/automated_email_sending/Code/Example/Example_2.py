# Databricks notebook source
# MAGIC %run /Workspace/Shared/BI/pipelines/adhoc/email_api/automated_email_sending

# COMMAND ----------

from IPython.display import display, HTML
import datetime
from dateutil.relativedelta import relativedelta
import pandas


# COMMAND ----------

# Get the current date
current_date = datetime.datetime.now()

# Subtract one month from the current date
previous_month = current_date - relativedelta(months=1)

# Get the previous month's full name (e.g., "March")
previous_month_name = previous_month.strftime('%B')
print(previous_month_name)

power_bi_link = "https://app.powerbi.com/groups/{GROUP_ID}/reports/{REPORT_ID}"

# COMMAND ----------

message =  f"""
Hi All,<br><br>
The <b>Power BI Cost Reporting</b> for <b>{previous_month_name}</b> is now <b>complete and available for review</b>. The report has been updated with the latest actuals and is ready for you to track <b>spend vs budget</b> for your areas of responsibility.<br><br>

<b>Access the Report Here:</b> <a href="{power_bi_link}">Link to PowerBI Dashboard</a><br><br>

This report enables you to;<br>
<ul>
    <li><b>Review actual spend vs budget</b> for your cost centres or business unit.</li>
    <li><b>Drill down into key variances</b> and identify areas requiring attention.</li>
    <li><b>Use MTD/YTD views</b> to compare financial performance over time.</li>
</ul><br>

For any queries, please reach out to your Finance Business Partner:<br>
<ul>
    <li><b>Managed Services:</b> Name 1</li>
    <li><b>SaaS:</b> Name 2</li>
    <li><b>Corporate Overheads:</b> Name 3</li>
</ul><br>

Thank you for using the Power BI Cost Reporting tool to manage and track financial performance. Please ensure you review your area’s financials and take any necessary actions.<br>
"""

# Print the HTML formatted content
display(HTML(message))


# COMMAND ----------

email_df = read_hive_table(HIVE_SAP_4_HANA, "s4h_email_key_lookup")
email_list = [row['Email'] for row in email_df.select('Email').collect()]
print(email_list)

# COMMAND ----------

new_items = ['Email_101@address.com', 'Email_102@address.com', 'Email_103@address.com']

for item in new_items:
    if item not in email_list:
        email_list.append(item)

print(email_list)


# COMMAND ----------

send_email_no_attachment(
    access_token=access_token,
    from_email='DataAnalytics@80hg.io',
    to_email=email_list,
    email_subject='Cost Center Reporting',
    content_type="HTML",
    content_body=message
)

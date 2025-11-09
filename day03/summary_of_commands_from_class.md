# useful commands we saw in lecture

import (statement is used to bring modules, packages, or specific objects (functions, classes, variables) from other modules into the current namespace, making them available for use. )

uv add (for adding liberies)
uv init מייצר אוטומטית קבצים שימושים כמו רידמי או סקיפט מרכזי, גרסא של פייתון ופיפרוגקט

cd (כניסה לכתובת של התיקיה הבאה שאכתוב)

len- פונקציה של פייתון על טקסט שמחזירה את האורך של המילה
word.lower - lower מציג או מחזיר את הטקסט כאותיות קטנות של הטקסט
יש עוד הרבה מתודות כאלה.

an example of creating for loop. range run from 1 to 4-1.
for n in range(1,4):
    print(n)


רץ בטווח כשהוא מתעלם ממספרים
for _ in range(1,4):
   [0] * (len2+1)
   # הלולאה הזו מייצרת וקטור של אפסים 
   
fruits=["apple","banna","cherry"]

zeros=[0]*3 # simillar command as zeros=[0,0,0]



בפייתון אפשר להחליף משתנים בדרך הבאה
## swap values
```python

    a=3
    b=6

    a , b = b , a # swap btw the values


בגדול פייתון עובד ככה:
יש את השפה המדוברת של פייתון
יש את הספריות שבאות יחד עם פייתון (הן לא חלק בסיסי של השפה)
ויש את הספריות שאנשים כותבים.


רוב מוחלט של הספריות השימושיות לצורך תכנות, מישהו כבר כתב.
לכן, להשתמש הסבפריות זה כלי יעיל.
על מנת להוריד ספריה צריך לכתוב בטרמינל 
"uv add braingloble_atlasapi" % שם של ספריה
על מנת לייעל קוד, צריך לכתוב בתיאור של הקוד באילו ספריות אני משתמש (תת נושא- תלויות
dependices)
מומךץ מאוד לשמור את התלויות השונות לכל פרוייקט במקום נפרד, שכן לפעמים אנשים מעדכנים את הספריות שלהם ואז אם אוריד את הגרסא החדשה יותר, אולי הפרוייקט הראשון שכתבתי לא יעבוד בגלל אותו עדכון.

אפשר גם לכתוב בקובץ נפרד את התלויות שיש לפרוייקט בספריות
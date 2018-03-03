### get user photo and download it, "bot" value must be available in the scope
```python
prof_pic_file_id = bot.get_user_profile_photos(update.message.from_user.id).photos[0][2].file_id
print prof_pic_file_id
profilePic = bot.get_file(prof_pic_file_id)
profilePic.download(str(update.message.from_user.id)+".jpg"
```
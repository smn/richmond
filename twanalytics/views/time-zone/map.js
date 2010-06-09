function(doc) {
  if(doc.user) {
      if(doc.user.time_zone == '') {
          emit('Unspecified', 1);
      } else {
          emit(doc.user.time_zone, 1);
      }
  }
}
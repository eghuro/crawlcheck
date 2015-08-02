// Copyright 2015 Alexandr Mansurov
#include "./RequestStorage.h"

const std::string RequestStorage::lock_response =
  "Cannot lock mutex on a response storage.";

const std::string RequestStorage::unlock_response =
  "Cannot unlock mutex on a response storage.";

const std::string RequestStorage::lock_request =
  "Cannot lock mutex on a request storage.";

const std::string RequestStorage::unlock_request =
  "Cannot unlock mutex on a request storage.";

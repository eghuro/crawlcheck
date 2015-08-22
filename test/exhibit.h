// Copyright 2015 alex
#ifndef TEST_EXHIBIT_H_
#define TEST_EXHIBIT_H_

class c {
 public:
   c() : x(-1) {}

   void setX(int val) {
     x = val;
   }

   int getX() {
     return x;
   }
 private:
   int x;
};

class b {
 public:
  b():params() {}
  virtual ~b() {}

  void setter(int x) {
    std::cout << params.getX() << std::endl;
    params.setX(x);
  }

 private:
  c params;
};
class a {
 public:
  a() {}
  virtual ~a() {
    for (auto it = vector.begin(); it != vector.end(); ++it) {
      delete (*it);
    }
  }
  void start() {
    create();
    call();
  }

  void create() {
    for (int i = 0; i < 1; i++) {
      vector.push_back(new b());
    }
  }

  void call() {
    for ( std::vector<b *>::iterator it = vector.begin(); it != vector.end(); ++it) {
      (*it) -> setter(1);
    }
  }

 private:
  std::vector<b *> vector;
};

#endif  // TEST_EXHIBIT_H_

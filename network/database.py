#!/usr/bin/python3


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy import create_engine, Column, Integer, String, Unicode, DateTime, ForeignKey, func


Base=declarative_base()
engine=create_engine("sqlite:///network.sqlite")
#engine=create_engine("sqlite:///junk.sqlite")
Session=sessionmaker(bind=engine)

class Namespace(Base):
	__tablename__ = "namespaces"

	nsname = Column(String,primary_key=True)
	interfaces = relationship("Interface",back_populates='namespace')

class Interface(Base):
	__tablename__ = "interfaces"

	ifindex = Column(Integer, primary_key=True)
	iflink  = Column(Integer)
	ifname  = Column(String)
	basename = Column(String)
	master  = Column(String)
	vid     = Column(Integer)
	address = Column(String)
	nsname  = Column(String, ForeignKey("namespaces.nsname"))
	namespace = relationship("Namespace",back_populates='interfaces')

def create():
	Base.metadata.create_all(engine)

if __name__ == "__main__":
	create()
	s=Session()
	n=Namespace(nsname="main")
	i=Interface(ifindex=1,nsname="main")
	s.add(n)
	s.add(i)
	s.commit()
	
	print("Hello")



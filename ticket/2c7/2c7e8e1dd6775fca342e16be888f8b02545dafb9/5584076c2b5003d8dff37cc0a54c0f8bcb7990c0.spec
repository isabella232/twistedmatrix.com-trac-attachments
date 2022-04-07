Summary: twistd
Name: Twisted
Version: 2.5.0
Release: %{?dist}.0
License: GPL
Group: System Environment/Libraries
URL: http://twistedmatrix.com/trac/
Source0: %{name}-%{version}.tar
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
Twisted is an event-driven networking engine written in Python and licensed under the MIT license.

%prep
%setup -q

%build
python setup.py build

%install
python setup.py install --root $RPM_BUILD_ROOT/ --prefix %{_prefix}

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{_bindir}/
%{_libdir}/
%{_prefix}/lib

%doc

%post

%postun

%changelog
* Wed Oct 31 2007  <vijay@meebo.com> - 
- Initial build.


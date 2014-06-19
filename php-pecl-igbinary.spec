# spec file for php-pecl-igbinary
#
# Copyright (c) 2010-2014 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/3.0/
#
# Please, preserve the changelog entries
#
%{!?php_inidir:  %{expand: %%global php_inidir  %{_sysconfdir}/php.d}}
%{!?php_incldir: %{expand: %%global php_incldir %{_includedir}/php}}
%{!?__pecl:      %{expand: %%global __pecl      %{_bindir}/pecl}}

%global extname   igbinary
%global with_zts  0%{?__ztsphp:1}
%global commit    c35d48f3d14794373b2ef89a6d79020bb7418d7f
%global short     %(c=%{commit}; echo ${c:0:7})
%global prever    -dev
%if "%{php_version}" < "5.6"
%global ini_name  %{extname}.ini
%else
%global ini_name  40-%{extname}.ini
%endif

Summary:        Replacement for the standard PHP serializer
Name:           php-pecl-igbinary
Version:        1.1.2
%if 0%{?short:1}
Release:        0.11.git%{short}%{?dist}
Source0:        https://github.com/%{extname}/%{extname}/archive/%{commit}/%{extname}-%{version}-%{short}.tar.gz
%else
Release:        3%{?dist}
Source0:        http://pecl.php.net/get/%{extname}-%{version}.tgz
# http://pecl.php.net/bugs/22598
Source1:        %{extname}-tests.tgz
%endif
# https://bugs.php.net/59669
License:        BSD
Group:          System Environment/Libraries

URL:            http://pecl.php.net/package/igbinary

# https://github.com/igbinary/igbinary/pull/24
Patch0:         igbinary-apcu.patch

BuildRequires:  php-pear
BuildRequires:  php-devel >= 5.2.0
# php-pecl-apcu-devel provides php-pecl-apc-devel
BuildRequires:  php-pecl-apc-devel >= 3.1.7

Requires(post): %{__pecl}
Requires(postun): %{__pecl}
Requires:       php(zend-abi) = %{php_zend_api}
Requires:       php(api) = %{php_core_api}

Provides:       php-%{extname} = %{version}
Provides:       php-%{extname}%{?_isa} = %{version}
Provides:       php-pecl(%{extname}) = %{version}
Provides:       php-pecl(%{extname})%{?_isa} = %{version}

%if 0%{?fedora} < 20
# Filter shared private
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}
%endif


%description
Igbinary is a drop in replacement for the standard PHP serializer.

Instead of time and space consuming textual representation, 
igbinary stores PHP data structures in a compact binary form. 
Savings are significant when using memcached or similar memory
based storages for serialized data.


%package devel
Summary:       Igbinary developer files (header)
Group:         Development/Libraries
Requires:      php-pecl-%{extname}%{?_isa} = %{version}-%{release}
Requires:      php-devel%{?_isa}

%description devel
These are the files needed to compile programs using Igbinary


%prep
%setup -q -c

%if 0%{?short:1}
mv igbinary-%{commit}/package.xml .
mv igbinary-%{commit} %{extname}-%{version}
sed -e '/release/s/-dev/dev/' -i package.xml

cd %{extname}-%{version}

%patch0 -p1 -b .apcu

%else
cd %{extname}-%{version}
tar xzf %{SOURCE1}
%endif

# Check version
extver=$(sed -n '/#define IGBINARY_VERSION/{s/.* "//;s/".*$//;p}' igbinary.h)
if test "x${extver}" != "x%{version}%{?prever}"; then
   : Error: Upstream version is ${extver}, expecting %{version}%{?prever}.
   exit 1
fi
cd ..

%if %{with_zts}
cp -r %{extname}-%{version} %{extname}-%{version}-zts
%endif

cat <<EOF | tee %{ini_name}
; Enable %{extname} extension module
extension=%{extname}.so

; Enable or disable compacting of duplicate strings
; The default is On.
;igbinary.compact_strings=On

; Use igbinary as session serializer
;session.serialize_handler=igbinary

; Use igbinary as APC serializer
;apc.serializer=igbinary
EOF


%build
cd %{extname}-%{version}
%{_bindir}/phpize
%configure --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}

%if %{with_zts}
cd ../%{extname}-%{version}-zts
%{_bindir}/zts-phpize
%configure --with-php-config=%{_bindir}/zts-php-config
make %{?_smp_mflags}
%endif


%install
make install -C %{extname}-%{version} \
     INSTALL_ROOT=%{buildroot}

install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml

install -D -m 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

# Install the ZTS stuff
%if %{with_zts}
make install -C %{extname}-%{version}-zts \
     INSTALL_ROOT=%{buildroot}
install -D -m 644 %{ini_name} %{buildroot}%{php_ztsinidir}/%{ini_name}
%endif

# Test & Documentation
cd %{extname}-%{version}
for i in $(grep 'role="test"' ../package.xml | sed -e 's/^.*name="//;s/".*$//')
do [ -f tests/$i ] && install -Dpm 644 tests/$i %{buildroot}%{pecl_testdir}/%{extname}/tests/$i
done
for i in $(grep 'role="doc"' ../package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 $i %{buildroot}%{pecl_docdir}/%{extname}/$i
done


%check
cd %{extname}-%{version}

# APC required for test 045
if [ -f %{php_extdir}/apcu.so ]; then
  MOD="-d extension=apcu.so"
elif [ -f %{php_extdir}/apc.so ]; then
  MOD="-d extension=apc.so"
fi

: simple NTS module load test, without APC, as optional
%{_bindir}/php --no-php-ini \
    --define extension=%{buildroot}%{php_extdir}/%{extname}.so \
    --modules | grep %{extname}

: upstream test suite
TEST_PHP_EXECUTABLE=%{_bindir}/php \
TEST_PHP_ARGS="-n $MOD -d extension=$PWD/modules/%{extname}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{_bindir}/php -n run-tests.php

%if %{with_zts}
cd ../%{extname}-%{version}-zts

: simple ZTS module load test, without APC, as optional
%{__ztsphp} --no-php-ini \
    --define extension=%{buildroot}%{php_ztsextdir}/%{extname}.so \
    --modules | grep %{extname}

: upstream test suite
TEST_PHP_EXECUTABLE=%{__ztsphp} \
TEST_PHP_ARGS="-n $MOD -d extension=$PWD/modules/%{extname}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__ztsphp} -n run-tests.php
%endif


%post
%{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :


%postun
if [ $1 -eq 0 ] ; then
    %{pecl_uninstall} %{extname} >/dev/null || :
fi


%files
%doc %{pecl_docdir}/%{extname}
%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{extname}.so
%{pecl_xmldir}/%{name}.xml

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{ini_name}
%{php_ztsextdir}/%{extname}.so
%endif


%files devel
%doc %{pecl_testdir}/%{extname}
%{php_incldir}/ext/%{extname}

%if %{with_zts}
%{php_ztsincldir}/ext/%{extname}
%endif


%changelog
* Thu Jun 19 2014 Remi Collet <rcollet@redhat.com> - 1.1.2-0.11.gitc35d48f
- rebuild for https://fedoraproject.org/wiki/Changes/Php56

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.2-0.10.gitc35d48f
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Apr 23 2014 Remi Collet <rcollet@redhat.com> - 1.1.2-0.9.gitc35d48f
- add numerical prefix to extension configuration file

* Mon Mar 10 2014 Remi Collet <rcollet@redhat.com> - 1.1.2-0.8.gitc35d48f
- cleanups and drop SCL support
- install doc in pecl_docdir
- install tests in pecl_testdir (devel)

* Mon Jul 29 2013 Remi Collet <rcollet@redhat.com> - 1.1.2-0.7.gitc35d48f
- adapt for scl

* Sat Jul 27 2013 Remi Collet <remi@fedoraproject.org> - 1.1.2-0.6.gitc35d48f
- latest snapshot
- fix build with APCu
- spec cleanups

* Fri Mar 22 2013 Remi Collet <rcollet@redhat.com> - 1.1.2-0.5.git3b8ab7e
- rebuild for http://fedoraproject.org/wiki/Features/Php55

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.2-0.4.git3b8ab7e
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.2-0.3.git3b8ab7e
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Apr 23 2012 Collet <remi@fedoraproject.org> - 1.1.2-0.2.git3b8ab7e
- enable ZTS extension

* Fri Jan 20 2012 Collet <remi@fedoraproject.org> - 1.1.2-0.1.git3b8ab7e
- update to git snapshot for php 5.4

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Sun Sep 18 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-3
- fix EPEL-6 build, no arch version for php-devel

* Sat Sep 17 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-2
- clean spec, adapted filters

* Mon Mar 14 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-1
- version 1.1.1 published on pecl.php.net
- rename to php-pecl-igbinary

* Mon Jan 17 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-1
- update to 1.1.1

* Fri Dec 31 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-3
- updated tests from Git.

* Sat Oct 23 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-2
- filter provides to avoid igbinary.so
- add missing %%dist

* Wed Sep 29 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-1
- initital RPM


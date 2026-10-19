project('gtasks',
  version: '0.1.0',
  meson_version: '>= 1.0.0',
)

dependency('gtk4')
dependency('libadwaita-1', version: '>= 1.8')
dependency('gtksourceview-5', version: '>= 5.10')
dependency('libspelling-1', version: '>= 0.4.10')

pkgdatadir = get_option('prefix') / get_option('datadir') / 'gtasks'
conf = configuration_data()
conf.set('PKGDATADIR', pkgdatadir)

configure_file(
  input: 'gtasks.in',
  output: 'gtasks',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: ['rwxr-xr-x'],
)

install_subdir('gtasks', install_dir: pkgdatadir)
subdir('data')

gnome = import('gnome')
gnome.post_install(glib_compile_schemas: true)

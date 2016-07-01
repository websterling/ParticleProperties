#! /usr/bin/env python

from lxml import etree
import sys

if sys.version < '3':
    import codecs
    input = raw_input

    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x


c = 2.9979e+11  # speed of light - milimeters per second
h_bar = 6.5821e-25  # in GeV sec

mcd2006 = etree.parse('2006mcd.xml')
mcd2014 = etree.parse('2014mcd.xml')
pythia8 = etree.parse('pythia8.xml')


def mcd2006_data(particle_identifier):
    super_plus = u('\u207a')
    super_minus = u('\u207b')

    for node in mcd2006.iter('particle'):
        identity = node.attrib.get('pdg-mc')
        if identity == particle_identifier:
            j = node.attrib.get('j')
            p = node.attrib.get('p')
            c = node.attrib.get('c')
            i = node.attrib.get('i')
            g = node.attrib.get('g')
            quarks = node.attrib.get('quarks')

            if j:
                left = 'J'
                right = j
            if not p and not c and not i:
                quantum_numbers = left + ' = ' + right
                return quantum_numbers, quarks
            if p:
                left = left + u('\u1d3e')
                if p is '+':
                    right = right + super_plus
                else:
                    right = right + super_minus
            if c:
                left = left + u('\u1d9c')
                if c is '+':
                    right = right + super_plus
                else:
                    right = right + super_minus
            if i:
                left = '(' + left + ')'
                right = '(' + right + ')'
                if g:
                    left = 'I' + u('\u1d33') + left
                    if g is '+':
                        right = i + super_plus + right
                    else:
                        right = i + super_minus + right
                else:
                    left = 'I' + left
                    right = i + right

            quantum_numbers = left + ' = ' + right
            quantum_numbers = quantum_numbers.replace('lt', '<')
            return quantum_numbers, quarks


def mcd2014_data(particle_identifier):
    for node in mcd2014.iter('particle'):
        identity = node.attrib.get('pdg-mc')
        if identity == particle_identifier:
            mass = node.attrib.get('massGeV')
            mass_error = node.attrib.get('massErrPlus')
            mass = mass + ' ' + u('\u00b1') + ' ' + mass_error[1:]
            chrg = node.attrib.get('chrg')
            width = node.attrib.get('widthGeV')
            if width:
                if width == '0.E+00':
                    lifetime = 'stable'
                else:
                    lifetime = '{:.3E}'.format(h_bar/float(width))
                    lifetime = str(lifetime) + ' s'
                    width_error = node.attrib.get('widthErrPlus')
                    if width_error:
                        width = width + ' ' + u('\u00b1') + ' ' + width_error[1:]
            if not width:
                for node in pythia8.iter('particle'):
                    identity = node.attrib.get('id')
                    if identity == particle_identifier:
                        tau0 = node.attrib.get('tau0')
                        if tau0:
                            lifetime = str(float(tau0) / c) + ' s'
                        else:
                            lifetime = 'no lifetime'
            return mass, width, chrg, lifetime


def pythia8_data(particle_identifier):
    decays = ''
    for node in pythia8.iter('particle'):
        identity = node.attrib.get('id')
        if identity == particle_identifier:
            name = node.attrib.get('name')
            anti_name = node.attrib.get('antiName')
            if not anti_name:
                anti_name = 'self'
            subfields = node.getchildren()
            total = 0.0
            decay_products = ''
            for subfield in subfields:
                decay_products = ''
                branching_ratio = subfield.attrib.get('bRatio')
                products = subfield.attrib.get('products').split()
                for product in products:
                    if int(product) < 0:
                        name_attrib = 'antiName'
                    else:
                        name_attrib = 'name'
                    product = product.replace('-', '')
                    for node in pythia8.iter('particle'):
                        identity = node.attrib.get('id')
                        if identity == product:
                            product_name = node.attrib.get(name_attrib)
                            decay_products = decay_products + product_name + ' '

                if '~' not in decay_products:
                    total += float(branching_ratio)
                    decays = decays + '\t' + branching_ratio + '\t' + decay_products + '\n'

            if len(decay_products) == 0:
                total = 'stable'

    return name, anti_name, decays, total


def index():
    index = {}
    full_list = []
    for node in pythia8.iter('particle'):
        pdg_mc = node.attrib.get('id')
        if len(pdg_mc) < 7:
            name = node.attrib.get('name')
            anti_name = node.attrib.get('antiName')
            if not anti_name:
                anti_name = 'self'
            index[int(pdg_mc)] = name, anti_name

    for key in sorted(index.keys()):
        full_list.append('%10s   %-17s%-22s' % (str(key), index[key][0], index[key][1]))

    if len(full_list) % 2 == 1:
        full_list.append('')

    for i in range(0, len(full_list)/2):
        print(full_list[i] + '\t' + full_list[i + len(full_list)/2])

    print('')
    return index


index = index()
particles = str(input('Input Particle Id(s): ')).split()
print('')

for particle_identifier in particles:
    if int(particle_identifier) in index:
        pass
    else:
        print(particle_identifier + ' is not a valid pdg-mc\n')
        quit()

    try:
        quantum_numbers, quarks = mcd2006_data(particle_identifier)
    except:
        print('Incomplete data on this particle\n')
        quit()

    mass, width, chrg, lifetime = mcd2014_data(particle_identifier)
    name, anti_name, decays, ratios_total = pythia8_data(particle_identifier)

    print('\t' + name + '\t\t' + quantum_numbers + '\t\tpdg-mc = ' + particle_identifier)
    print('\tCharge = ' + chrg + '\tAnitparticle = ' + anti_name + '\n')

    print('\tMass m = ' + mass + ' GeV')
    if width:
        print('\tFull width ' + u('\u0393') + ' = ' + width + ' GeV')

    print('\tMean lifetime = ' + lifetime)

    if quarks:
        print('\tQuarks = ' + quarks)

    if decays:
        print('\n\tDecay modes\n\tFraction\tProducts')
        print(decays.rstrip())
        if ratios_total:
            print('\t' + str(ratios_total) + '\t\tTotal')

    print('\n')

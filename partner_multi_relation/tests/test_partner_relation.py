# -*- coding: utf-8 -*-
# Copyright 2016-2018 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import date
from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import ValidationError

from .common import PartnerRelationCase


class TestPartnerRelation(PartnerRelationCase):
    """Run tests on the base model res.partner.relation.

    Do not use res.partner.relation.all in this class.
    """

    post_install = True

    # pylint: disable=invalid-name
    def setUp(self):
        super(TestPartnerRelation, self).setUp()
        # Create a relation type having no particular conditions.
        self.type_school2student = self.type_model.create({
            'name': 'school has student',
            'name_inverse': 'studies at school'})
        # Create partners.
        self.partner_school = self.partner_model.create({
            'name': 'Test School',
            'is_company': True,
            'ref': 'TS'})
        self.partner_bart = self.partner_model.create({
            'name': 'Bart Simpson',
            'is_company': False,
            'ref': 'BS'})
        self.partner_lisa = self.partner_model.create({
            'name': 'Lisa Simpson',
            'is_company': False,
            'ref': 'LS'})
        # Create relations based on those conditions.
        self.relation_school2bart = self.relation_model.create({
            'left_partner_id': self.partner_school.id,
            'type_id': self.type_school2student.id,
            'right_partner_id': self.partner_bart.id})
        self.assertTrue(self.relation_school2bart)
        self.relation_school2lisa = self.relation_model.create({
            'left_partner_id': self.partner_school.id,
            'type_id': self.type_school2student.id,
            'right_partner_id': self.partner_lisa.id})
        self.assertTrue(self.relation_school2lisa)

    def test_selection_name_search(self):
        """Test wether we can find type selection on reverse name."""
        selection_types = self.selection_model.name_search(
            name=self.selection_person_is_employee.name)
        self.assertTrue(selection_types)
        self.assertTrue(
            (self.selection_person_is_employee.id,
             self.selection_person_is_employee.name) in selection_types)

    def test_self_allowed(self):
        """Test creation of relation to same partner when type allows."""
        type_allow = self.type_model.create({
            'name': 'allow',
            'name_inverse': 'allow_inverse',
            'contact_type_left': 'p',
            'contact_type_right': 'p',
            'allow_self': True})
        self.assertTrue(type_allow)
        reflexive_relation = self.relation_model.create({
            'type_id': type_allow.id,
            'left_partner_id': self.partner_person_test.id,
            'right_partner_id': self.partner_person_test.id})
        self.assertTrue(reflexive_relation)

    def test_self_disallowed(self):
        """Test creating relation to same partner when disallowed.

        Attempt to create a relation of a partner to the same partner should
        raise an error when the type of relation explicitly disallows this.
        """
        type_disallow = self.type_model.create({
            'name': 'disallow',
            'name_inverse': 'disallow_inverse',
            'contact_type_left': 'p',
            'contact_type_right': 'p',
            'allow_self': False})
        self.assertTrue(type_disallow)
        with self.assertRaises(ValidationError):
            self.relation_model.create({
                'type_id': type_disallow.id,
                'left_partner_id': self.partner_person_test.id,
                'right_partner_id': self.partner_person_test.id})

    def test_self_disallowed_after_self_relation_created(self):
        """Test that allow_self can not be true if a reflexive relation
        already exists.

        If at least one reflexive relation exists for the given type,
        reflexivity can not be disallowed.
        """
        type_allow = self.type_model.create({
            'name': 'allow',
            'name_inverse': 'allow_inverse',
            'contact_type_left': 'p',
            'contact_type_right': 'p',
            'allow_self': True})
        self.assertTrue(type_allow)
        reflexive_relation = self.relation_model.create({
            'type_id': type_allow.id,
            'left_partner_id': self.partner_person_test.id,
            'right_partner_id': self.partner_person_test.id})
        self.assertTrue(reflexive_relation)
        with self.assertRaises(ValidationError):
            type_allow.allow_self = False

    def test_self_default(self):
        """Test default not to allow relation with same partner.

        Attempt to create a relation of a partner to the same partner
        raise an error when the type of relation does not explicitly allow
        this.
        """
        type_default = self.type_model.create({
            'name': 'default',
            'name_inverse': 'default_inverse',
            'contact_type_left': 'p',
            'contact_type_right': 'p'})
        self.assertTrue(type_default)
        with self.assertRaises(ValidationError):
            self.relation_model.create({
                'type_id': type_default.id,
                'left_partner_id': self.partner_person_test.id,
                'right_partner_id': self.partner_person_test.id})

    def test_self_mixed(self):
        """Test creation of relation with wrong types.

        Trying to create a relation between partners with an inappropiate
        type should raise an error.
        """
        with self.assertRaises(ValidationError):
            self.relation_model.create({
                'type_id': self.relation_type_company_has_employee.id,
                'left_partner_id': self.partner_person_test.id,
                'right_partner_id': self.partner_company_test.id})

    def test_symmetric(self):
        """Test creating symmetric relation."""
        # Start out with non symmetric relation:
        type_symmetric = self.type_model.create({
            'name': 'not yet symmetric',
            'name_inverse': 'the other side of not symmetric',
            'is_symmetric': False,
            'contact_type_left': False,
            'contact_type_right': 'p'})
        # not yet symmetric relation should result in two records in
        # selection:
        selection_symmetric = self.selection_model.search([
            ('type_id', '=', type_symmetric.id)])
        self.assertEqual(len(selection_symmetric), 2)
        # Now change to symmetric and test name and inverse name:
        with self.env.do_in_draft():
            type_symmetric.write({
                'name': 'sym',
                'is_symmetric': True})
        self.assertEqual(type_symmetric.is_symmetric, True)
        self.assertEqual(
            type_symmetric.name_inverse,
            type_symmetric.name)
        self.assertEqual(
            type_symmetric.contact_type_right,
            type_symmetric.contact_type_left)
        # now update the database:
        type_symmetric.write({
            'name': type_symmetric.name,
            'is_symmetric': type_symmetric.is_symmetric,
            'name_inverse': type_symmetric.name_inverse,
            'contact_type_right': type_symmetric.contact_type_right})
        # symmetric relation should result in only one record in
        # selection:
        selection_symmetric = self.selection_model.search([
            ('type_id', '=', type_symmetric.id)])
        self.assertEqual(len(selection_symmetric), 1)

    def test_category_domain(self):
        """Test check on category in relations."""
        # Check on left side:
        with self.assertRaises(ValidationError):
            self.relation_model.create({
                'type_id': self.relation_type_ngo_has_volunteer.id,
                'left_partner_id': self.partner_company_test.id,
                'right_partner_id': self.partner_volunteer_test.id})
        # Check on right side:
        with self.assertRaises(ValidationError):
            self.relation_model.create({
                'type_id': self.relation_type_ngo_has_volunteer.id,
                'left_partner_id': self.partner_ngo_test.id,
                'right_partner_id': self.partner_person_test.id})

    def test_display_name(self):
        """Test display name"""
        relation = self.relation_company2employee
        self.assertEqual(
            relation.display_name, '%s %s %s' % (
                relation.left_partner_id.name,
                relation.type_id.name,
                relation.right_partner_id.name))

    def test_relation_type_change(self):
        """Test change in relation type conditions."""
        # Create a relation that will be made invalid.
        relation_bart2lisa = self.relation_model.create({
            'left_partner_id': self.partner_bart.id,
            'type_id': self.type_school2student.id,
            'right_partner_id': self.partner_lisa.id})
        self.assertTrue(relation_bart2lisa)
        # Create a category and make it a condition for the
        #     relation type.
        # - Test restriction
        # - Test ignore
        category_student = self.category_model.create({'name': 'Student'})
        with self.assertRaises(ValidationError):
            self.type_school2student.write({
                'partner_category_right': category_student.id})
        self.assertFalse(self.type_school2student.partner_category_right.id)
        self.type_school2student.write({
            'handle_invalid_onchange': 'ignore',
            'partner_category_right': category_student.id})
        self.assertEqual(
            self.type_school2student.partner_category_right.id,
            category_student.id)
        # Fourth make company type a condition for left partner
        # - Test ending
        # - Test deletion
        self.partner_bart.write({
            'category_id': [(4, category_student.id)]})
        self.partner_lisa.write({
            'category_id': [(4, category_student.id)]})
        # Future student to be deleted by end action:
        partner_homer = self.partner_model.create({
            'name': 'Homer Simpson',
            'is_company': False,
            'ref': 'HS',
            'category_id': [(4, category_student.id)]})
        relation_lisa2homer = self.relation_model.create({
            'left_partner_id': self.partner_lisa.id,
            'type_id': self.type_school2student.id,
            'right_partner_id': partner_homer.id,
            'date_start': fields.Date.to_string(
                date.today() + relativedelta(months=+6))})
        self.assertTrue(relation_lisa2homer)
        self.type_school2student.write({
            'handle_invalid_onchange': 'end',
            'contact_type_left': 'c'})
        self.assertEqual(
            relation_bart2lisa.date_end, fields.Date.today())
        # Future relations that became invalid should be deleted.
        self.assertFalse(relation_lisa2homer.exists())
        self.type_school2student.write({
            'handle_invalid_onchange': 'delete',
            'contact_type_left': 'c',
            'contact_type_right': 'p'})
        self.assertFalse(relation_bart2lisa.exists())

    def test_relation_type_unlink_dberror(self):
        """Test deleting relation type when not possible.

        This test will catch a DB Integrity error. Because of that the
        cursor will be invalidated, and further tests using the objects
        will not be possible.
        """
        # Create a relation type having restrict particular conditions.
        self.type_school2student.handle_invalid_onchange = 'restrict'
        # Unlink should lead to error because of restrict:
        with self.assertRaises(IntegrityError):
            self.type_school2student.unlink()

    def test_relation_type_unlink(self):
        """Test delete of relation type, including deleting relations."""
        # First create a relation type having restrict particular conditions.
        self.type_school2student.handle_invalid_onchange = 'delete'
        # Delete type. Relations with type should also cease to exist:
        self.type_school2student.unlink()
        self.assertFalse(self.relation_school2bart.exists())

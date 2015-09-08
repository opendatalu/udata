<style lang="less">
.form-control {
    color: #555;
}
</style>

<template>
    <form role="form">
        <form-field v-repeat="field:fields"
            schema="{{schema}}" model="{{model}}">
        </form-field>
    </form>
</template>

<script>
'use strict';

var BaseForm = require('components/form/base-form');

module.exports = {
    name: 'form-vertical',
    mixins: [BaseForm],
    components: {
        'form-field': require('components/form/vertical-field.vue')
    }
};
</script>

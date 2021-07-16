<template>
  <v-autocomplete 
    :label="label"
    :value="value"
    @input="$emit('input', $event)"
    :loading="loading"
    :items="result"
    @update:search-input="search"
    hide-no-data
    hide-details
    no-filter
    item-value="username"
    item-text="username"
    :append-icon="readonly ? 'mdi-pencil-off-outline': ''"
    :readonly="readonly"
    :outlined="!readonly">
  </v-autocomplete>
</template>
<script lang="ts">
import Vue from 'vue';

import { User } from '../store/models';

export default Vue.extend({
  name: 'HinkUserInput',
  props: {
    value: {
      type: String,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    label: {
      type: String,
      default: 'Username',
    },
  },
  data: () => ({
    prevSearch: '',
  }),
  computed: {
    loading(): boolean {
      return this.$store.getters['users/status'] === 'loading';
    },
    result(): User[] {
      return this.$store.getters['users/searchResult'];
    },
  },
  methods: {
    search(val: string) {
      if (this.prevSearch !== val && !this.loading) {
        this.$store.dispatch('users/search', { username: val || this.value })
          .catch(err => this.$store.commit('snackbar/showError', err));
        this.prevSearch=val;
      }
    },
  }
})
</script>

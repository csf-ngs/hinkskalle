<template>
  <div class="tokens">
    <v-container>
      <v-row justify="center">
        <v-col cols="6">
          <h1 class="display-1 text-center">Tokens</h1>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="10">
          <v-data-table
            id="tokens"
            :headers="headers"
            :items="tokens"
            :loading="loading">
            <template v-slot:item.createdAt="{ item }">
              {{item.createdAt | moment('YYYY-MM-DD HH:mm:ss')}}
            </template>
          </v-data-table>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';

export default Vue.extend({
  name: 'Tokens',
  mounted() {
    this.loadTokens();
  },
  data: () => ({
    headers: [
      { text: 'id', value: 'id', },
      { text: 'Token', value: 'token', sortable: true, },
      { text: 'Created', value: 'createdAt', sortable: true, },
      { text: 'Deleted', value: 'deleted', sortable: false, },
    ],
  }),
  computed: {
    tokens() {
      return this.$store.getters['tokens/tokens'];
    },
    loading() {
      return this.$store.getters['tokens/status']==='loading';
    },
  },
  methods: {
    loadTokens() {
      this.$store.dispatch('tokens/list');
    },
  },
});
</script>
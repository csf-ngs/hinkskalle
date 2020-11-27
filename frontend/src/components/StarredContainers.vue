<template>
  <v-container>
    <v-row>
      <v-col>
        <h2>Starred Containers</h2>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" v-for="container in containers" :key="container.id">
        <v-card outlined raised class="x-container" :to="{ name: 'ContainerDetails', params: { entity: container.entityName, collection: container.collectionName, container: container.name } }">
          <v-card-title class="text-h6">
            {{container.fullPath}}
          </v-card-title>
          <v-card-text>
            {{container.description}}
          </v-card-text>
          <v-card-actions>
            <v-spacer>
            </v-spacer>
            <v-icon @click.stop.prevent="copyTag(container)">mdi-content-copy</v-icon>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
<script lang="ts">
import { Container } from '@/store/models';
import Vue from 'vue';

export default Vue.extend({
  name: 'StarredContainers',
  mounted() {
    this.loadStarred();
  },
  computed: {
    containers(): Container[] {
      return this.$store.getters['users/starred'];
    }
  },
  methods: {
    loadStarred() {
      this.$store.dispatch('users/getStarred')
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    copyTag(container: Container) {
      this.$copyText(`library://${container.fullPath}`)
        .then(() => this.$store.commit('snackbar/open', 'Copied to clipboard'));
    },
  }
});
</script>